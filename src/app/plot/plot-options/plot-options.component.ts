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

  // public plotObject: any;
  public metadata: ObjectMetadata;
  public plotTypeData: Array<Select2OptionData> = [{id: '', text: ''}];
  // public formDimensions: FormArray;
  public dimensionData: Array<Select2OptionData> = [];
  private listPlotTypes: any;
  public selectedPlotType: any;
  public axisBlocks: any[];
  public selectedPlotTypeId: string; // for select2
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
        console.log('PLOT METADATA', this.metadata);

        // get list of plot types from server
        this.getPlotTypes();

        // set title and dimensions
        this.plotService.setConfig(
          result.data_type.oterm_name,
          result.dim_context.length,
          (dims: Dimension[]) => {
            this.dimensions = dims;
          }
        );

        // get dropdown values for dimensions
        result.dim_context.forEach(dim => {
          this.dimensionData.push({
            id: this.dimensionData.length.toString(),
            text: dim.data_type.oterm_name
          });
        });

        // add dropdown value for data measurements
        this.dimensionData.push({
          id: this.dimensionData.length.toString(),
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
        console.log('DATA', data);
        this.listPlotTypes = data.results.filter((val, idx) => {
          return val.n_dimensions === this.metadata.dim_context.length;
        });
        console.log('LIST PLOT TYPES');

        // add plot type values to select2
        this.plotTypeData = [{id: '', text: ''}, ...this.listPlotTypes.map((val, idx) => {
          return { id: idx.toString(), text: val.name }; }
        )];
        console.log('PLOT TYPE DATA');

        // add icons for each plot type
        this.listPlotTypes.forEach(plotType => {
          this.plotIcons[plotType.name] = plotType.image_tag;
        });
      });
  }

  updatePlotType(event) {
    if (event.value.length) {
      const n = parseInt(event.value, 10);
      console.log('LIST PLOT TYPES', this.listPlotTypes, this.listPlotTypes[n], n, event.value);
      const { plotly_trace, plotly_layout, axis_blocks } = this.listPlotTypes[n];
      this.plotBuilder.plotly_trace = plotly_trace;
      this.plotBuilder.plotly_layout = plotly_layout;
      this.axisBlocks = axis_blocks;
      this.selectedPlotType = this.listPlotTypes[n];
      console.log('AXIS BLOCKS', this.axisBlocks);
    }
  }

  onGoBack(id) {
    // this.plotService.resetValues();
    this.router.navigate([`/search/result/${id}`]);
  }

  // ngOnInit() {

  //   // set up plot builder value from service
  //   this.plotBuilder = this.plotService.getPlotBuilder();

  //   // get object id
  //   this.route.params.subscribe(params => {
  //     this.objectId = params.id;

  //     // get metadata
  //     this.queryBuilder.getObjectMetadata(this.objectId)
  //       .subscribe((result: any) => {
  //         this.metadata = result;
  //         console.log('PLOT METADATA', this.metadata);
  //         // this.plotBuilder.title = result.data_type.oterm_name;
  //         // this.plotService.setDimensions(result.dim_context.length);
  //         this.plotBuilder.setConfig(
  //           result.data_type.oterm_name,
  //           result.dim_context.length
  //           );

  //         // add plot object dimensions to form
  //         result.dim_context.forEach(dim => {
  //           this.plotBuilder.dimensions.push(new Dimension());
  //           console.log('DIM', dim);
  //           this.dimensionData.push({
  //             id: this.dimensionData.length.toString(),
  //             text: dim.data_type.oterm_name
  //           });
  //         });

  //         // add one more dimension for data values
  //         this.plotBuilder.dimensions.push(new Dimension());
  //         this.dimensionData.push({
  //           id: this.dimensionData.length.toString(),
  //           text: result.typed_values[0].value_type.oterm_name
  //         });

  //         console.log('PLOT BUILDER', this.plotBuilder);

  //         // add object dimension values to each dimension category
  //         const measurements = result.typed_values[0];
  //         // this.plotObject.dimensions.push({
  //         //   type: measurements.value_type.oterm_name,
  //         //   dim_vars: [measurements.value_type.oterm_name]
  //         // });

  //         // get plot types from server
  //         this.getPlotTypes();
  //             // if (this.plotService.plotForm && this.plotService.plotType) {
  //             //   this.populatePlotForm();
  //             // }
  //         });
  //       });
  //   }

  //   test() {
  //     console.log(this.plotBuilder, this.metadata);
  //   }

  // getPlotTypes() {
  //   this.plotService.getPlotTypes()
  //     .subscribe((data: any) => {
  //       // filter plot types by n_dimension
  //       this.listPlotTypes = data.results.filter((val, idx) => {
  //         return val.n_dimensions === this.metadata.dim_context.length;
  //       });

  //       // add plot type values to select2
  //       this.plotTypeData = [{id: '', text: ''}, ...this.listPlotTypes.map((val, idx) => {
  //         return { id: idx.toString(), text: val.name }; }
  //       )];

  //       // add icons for each plot type
  //       this.listPlotTypes.forEach(plotType => {
  //         this.plotIcons[plotType.name] = plotType.image_tag;
  //       });
  //     });
  // }

  // updatePlotType(event) {
  //   const n = parseInt(event.value, 10);
  //   this.selectedPlotType = this.listPlotTypes[n];
  // }

  // populatePlotForm() {
  //   this.plotForm = this.plotService.plotForm;
  //   this.selectedPlotType = this.plotService.plotType;
  //   this.selectedPlotTypeId = this.plotTypeData.find(item => {
  //     return item.text === this.selectedPlotType.name;
  //   }).id;
  // }

  // addDimensions(index) {
  //   if (index) {
  //     this.formDimensions = this.plotForm.get('dimensions') as FormArray;

  //     // clear old values from previous plot types
  //     if (!this.plotService.plotForm) {
  //       while (this.formDimensions.value.length) {
  //         this.formDimensions.removeAt(0);
  //       }
  //     }
  //     // add N new dimensions from selected plot type
  //     this.selectedPlotType = this.listPlotTypes[index];
  //     // for (const _ of this.selectedPlotType.axis_blocks) {
  //     //   this.formDimensions.push(this.createDimensionItem());
  //     // }

  //     this.selectedPlotType.axis_blocks.forEach((v, i) => {
  //       if (!this.plotService.plotForm || v.hasOwnProperty('displayValuesFrom')) {
  //         this.formDimensions.push(this.createDimensionItem(this.plotForm.value.dimensions[i])) ;
  //       }
  //     });
  //   }
  // }

  // createDimensionItem(dim) {
  //   return this.fb.group({
  //     fromDimension: '',
  //     displayValuesFrom: this.fb.array([]),
  //     displayAxisLabels: true,
  //     displayAxisLabelsAs: this.fb.array([]),
  //     displayHoverLabels: true,
  //     displayHoverLabelsAs: '',
  //     displayAxisTitle: true,
  //     axisTitle: ''
  //   });
  // }

  // submit() {
  //   // this.plotService.submitNewPlot(this.plotForm, this.metadata, this.selectedPlotType);
  // }

  // onGoBack(id) {
  //   this.plotService.resetValues();
  //   this.router.navigate([`search/result/${id}`]);
  // }


}
