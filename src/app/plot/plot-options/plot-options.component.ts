import { Component, OnInit, Output, EventEmitter } from '@angular/core';
import { Router, ActivatedRoute, NavigationEnd } from '@angular/router';
import { PlotService } from '../../shared/services/plot.service';
import { ObjectMetadata } from '../../shared/models/object-metadata';
import { QueryBuilderService } from '../../shared/services/query-builder.service';
import { Select2OptionData } from 'ng2-select2';
import { PlotBuilder, Dimension } from '../../shared/models/plot-builder';
import { PlotlyConfig, AxisBlock } from 'src/app/shared/models/plotly-config';

@Component({
  selector: 'app-plot-options',
  templateUrl: './plot-options.component.html',
  styleUrls: ['./plot-options.component.css'],
})
export class PlotOptionsComponent implements OnInit {

  public metadata: ObjectMetadata;
  public plotTypeData: Array<Select2OptionData> = [{id: '', text: ''}];
  public plotTypeDataValue: string; // for select2
  public dimensionData: Array<Select2OptionData> = [];
  public listPlotTypes: PlotlyConfig[];
  public selectedPlotType: PlotlyConfig;
  public axisBlocks: AxisBlock[];
  public objectId: string;
  public plotBuilder: PlotBuilder;
  public dimensions: Dimension[];
  public plotIcons = {};
  public previousUrl: string;
  @Output() updated: EventEmitter<any> = new EventEmitter();
  currentUrl: string;
  isEditor = false; // determines whether component is in plot/options or plot/result

  public plotTypeOptions: Select2Options = {
    width: '100%',
    containerCssClass: 'select2-custom-container',
    templateResult: state => {
      if (!state.id) {
        return state;
      }
      return `${this.plotIcons[state.text]} <span>${state.text}</span>`;
    },
    escapeMarkup: m => m
  };

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
            // result.data_type.oterm_name,
            // result.dim_context.length,
            result,
            (dims: Dimension[]) => {
              this.dimensions = dims;
            }
          );
        } else {
          // use old plot config (coming back from /result)
          this.plotTypeDataValue = plotType;
          this.dimensions = this.plotService.getConfiguredDimensions();
        }

        // get dropdown values for dimensions
        result.dim_context.forEach(dim => {
          this.dimensionData.push({
            id: this.dimensionData.length.toString(),
            text: dim.data_type.oterm_name
          });
        });
        // add dropdown value for data measurements
        this.dimensionData.push({
          // id: this.dimensionData.length.toString(),
          id: 'D',
          text: result.typed_values[0].value_type.oterm_name
        });
      });
  }

    test() {
    }

    getPlotTypes() {
    this.plotService.getPlotTypes()
      .subscribe((data: any) => {
        // filter plot types by n_dimension
        this.listPlotTypes = data.results.filter((val, idx) => {
          return val.n_dimensions === this.metadata.dim_context.length;
        });

        // add plot type values to select2
        this.plotTypeData = [{id: '', text: ''}, ...this.listPlotTypes.map((val, idx) => {
          return { id: idx.toString(), text: val.name }; }
        )];

        // add icons for each plot type
        this.listPlotTypes.forEach(plotType => {
          this.plotIcons[plotType.name] = plotType.image_tag;
        });
      });
  }

  updatePlotType(event) {
    if (event.value.length) {
      const n = parseInt(event.value, 10);
      const { plotly_trace, plotly_layout, axis_blocks } = this.listPlotTypes[n];
      this.plotBuilder.plotly_trace = plotly_trace;
      this.plotBuilder.plotly_layout = plotly_layout;
      this.axisBlocks = axis_blocks;
      this.selectedPlotType = this.listPlotTypes[n];
      this.plotService.setPlotType(event.value);
    }
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
