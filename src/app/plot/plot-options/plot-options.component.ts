import { Component, OnInit, Output, EventEmitter } from '@angular/core';
import { Router, ActivatedRoute, NavigationEnd } from '@angular/router';
import { PlotService } from '../../shared/services/plot.service';
import { ObjectMetadata } from '../../shared/models/object-metadata';
import { QueryBuilderService } from '../../shared/services/query-builder.service';
import { PlotBuilder, Dimension } from '../../shared/models/plot-builder';
import { PlotlyConfig, AxisBlock } from 'src/app/shared/models/plotly-config';
@Component({
  selector: 'app-plot-options',
  templateUrl: './plot-options.component.html',
  styleUrls: ['./plot-options.component.css'],
})
export class PlotOptionsComponent implements OnInit {

  public metadata: ObjectMetadata;
  public plotTypeData: PlotlyConfig[];
  public dimensionData: any[];
  public selectedPlotType: PlotlyConfig;
  public axisBlocks: AxisBlock[];
  public objectId: string;
  public plotBuilder: PlotBuilder;
  public dimensions: Dimension[];
  public previousUrl: string;
  @Output() updated: EventEmitter<any> = new EventEmitter();
  currentUrl: string;
  isEditor = false; // determines whether component is in plot/options or plot/result

  constructor(
    private route: ActivatedRoute,
    private plotService: PlotService,
    private queryBuilder: QueryBuilderService,
    private router: Router,
    ) {
      this.router.events.subscribe(event => {
        if (event instanceof NavigationEnd) {
          this.currentUrl = event.url;
          this.isEditor = event.url.includes('result');
        }
      });
    }

  ngOnInit() {

    this.previousUrl = this.queryBuilder.getPreviousUrl();

    // set up plot builder value from service;
    this.plotBuilder = this.plotService.getPlotBuilder();

    // get object id
    this.route.params.subscribe(params => {
      this.objectId = params.id;
      this.plotBuilder.objectId = params.id;
    });

    // get metadata
    this.queryBuilder.getObjectMetadata(this.objectId)
      .subscribe((result: ObjectMetadata) => {
        this.metadata = result;

        // get list of plot types from server
        this.getPlotTypes();

        // set title and dimensions
        const plotType = this.plotService.getPlotType();
        if (!plotType) {
          // create new plot config
          this.plotService.setConfig(
            result,
            (dims: Dimension[]) => {
              this.dimensions = dims;
            }
          );
        } else {
          // use old plot config (coming back from /result)
          this.selectedPlotType = plotType;
          this.axisBlocks = plotType.axis_blocks;
          this.dimensions = this.plotService.getConfiguredDimensions();
        }
      });
  }

    getPlotTypes() {
    this.plotService.getPlotTypes()
      .subscribe((data: any) => {
        // filter plot types by n_dimension
        this.plotTypeData = data.results.filter((val, idx) => {
          return val.n_dimensions === this.metadata.dim_context.length;
        });
      });
  }

  updatePlotType(event: PlotlyConfig) {
    this.plotBuilder.plotly_trace = event.plotly_trace;
    this.plotBuilder.plotly_layout = event.plotly_layout;
    this.axisBlocks = event.axis_blocks;
    this.selectedPlotType = event;
    this.plotService.setPlotType(event);
  }

  submitPlot() {
    this.plotService.setPlotCache();
    if (this.isEditor) {
      this.updated.emit();
    } else {
      this.router.navigate([`plot/result/${this.objectId}`]);
    }
  }

  onGoBack(id) {
    this.plotService.clearPlotBuilder();
    const url = this.previousUrl ? this.previousUrl : `/search/result/brick/${id}`;
    this.router.navigate([url]);
  }

}
