import { Component, OnInit } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
import { PlotService } from '../../shared/services/plot.service';
import { ObjectMetadata } from '../../shared/models/object-metadata';
import { QueryBuilderService } from '../../shared/services/query-builder.service';
import { Select2OptionData } from 'ng2-select2';
import { FormBuilder, FormGroup, FormControl, FormArray } from '@angular/forms';
import { PlotBuilder, Dimension } from '../../shared/models/plot-builder';
import * as _ from 'lodash';

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
  private listPlotTypes: any;
  public selectedPlotType: any;
  public axisBlocks: any[];
  public objectId: string;
  public plotBuilder: PlotBuilder;
  public dimensions: Dimension[];
  public plotIcons = {};

  public plotTypeOptions: Select2Options = {
    width: '100%',
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
    ) { }

  ngOnInit() {
    // set up plot builder value from service;
    this.plotBuilder = this.plotService.getPlotBuilder();

    // get object id
    this.route.params.subscribe(params => {
      this.objectId = params.id;
      this.plotBuilder.objectId = params.id;
    });

    // get metadata
    this.queryBuilder.getObjectMetadata(this.objectId)
      .subscribe((result: any) => {
        this.metadata = result;
        this.plotBuilder.config.title = result.data_type.oterm_name;

        // get list of plot types from server
        this.getPlotTypes();

        // set title and dimensions
        const plotType = this.plotService.getPlotType();
        if (!plotType) {
          // create new plot config
          this.plotService.setConfig(
            result.data_type.oterm_name,
            result.dim_context.length,
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
      console.log('COMPONENT', this.plotBuilder, this.metadata);
      console.log('SERVICE', this.plotService.plotBuilder);
      console.assert(_.isEqual(this.plotBuilder, this.plotService.plotBuilder));
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

  onGoBack(id) {
    // this.plotService.resetValues();
    this.plotService.clearPlotBuilder();
    this.router.navigate([`/search/result/${id}`]);
  }

}
