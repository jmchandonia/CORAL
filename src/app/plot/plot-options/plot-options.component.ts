import { Component, OnInit } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
import { PlotService } from '../../shared/services/plot.service';
import { ObjectMetadata } from '../../shared/models/object-metadata';
import { QueryBuilderService } from '../../shared/services/query-builder.service';
import { Select2OptionData } from 'ng2-select2';
import { FormBuilder, FormGroup, FormControl, FormArray } from '@angular/forms';
import { PlotBuilder, Dimension } from '../../shared/models/plot-builder';

@Component({
  selector: 'app-plot-options',
  templateUrl: './plot-options.component.html',
  styleUrls: ['./plot-options.component.css'],
})
export class PlotOptionsComponent implements OnInit {

  // public plotObject: any;
  public plotMetadata: ObjectMetadata;
  public plotTypeData: Array<Select2OptionData> = [{id: '', text: ''}];
  public formDimensions: FormArray;
  private testForm: any;
  private listPlotTypes: any;
  public selectedPlotType: any;
  public selectedPlotTypeId: string; // for select2
  public objectId: string;
  public plotBuilder: PlotBuilder;

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

    // set up plot builder value from service
    this.plotBuilder = this.plotService.plotBuilder;

    // get object id
    this.route.params.subscribe(params => {
      this.objectId = params.id;

      // get metadata
      this.queryBuilder.getObjectMetadata(this.objectId)
        .subscribe((result: any) => {
          this.plotMetadata = result;
          console.log('PLOT METADATA', this.plotMetadata);
          this.plotBuilder.title = result.data_type.oterm_name;

          // add plot object dimensions to form
          result.dim_context.forEach(dim => {
            this.plotBuilder.dimensions.push(new Dimension());
          });

          console.log('PLOT BUILDER', this.plotBuilder);

          // add object dimension values to each dimension category
          const measurements = result.typed_values[0];
          // this.plotObject.dimensions.push({
          //   type: measurements.value_type.oterm_name,
          //   dim_vars: [measurements.value_type.oterm_name]
          // });

          // get plot types from server
          this.plotService.getPlotTypes()
            .subscribe((data: any) => {

              // filter plot types by n_dimension
              this.listPlotTypes = data.results.filter((val, idx) => {
                return val.n_dimensions === this.plotMetadata.dim_context.length;
              });

              // add plot type values to select2
              this.plotTypeData = [{id: '', text: ''}, ...this.listPlotTypes.map((val, idx) => {
                return { id: idx.toString(), text: val.name }; }
              )];

              // add icons for each plot type
              this.listPlotTypes.forEach(plotType => {
                this.plotIcons[plotType.name] = plotType.image_tag;
              });

              // if (this.plotService.plotForm && this.plotService.plotType) {
              //   this.populatePlotForm();
              // }
          });
        });
    });
  }

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

  // updatePlotType(event) {
  //   if (event.value !== '-1') {
  //     this.plotForm.controls.plotType.setValue(event.data[0].text);
  //     this.addDimensions(event.value);
  //   }
  // }

  submit() {
    // this.plotService.submitNewPlot(this.plotForm, this.plotMetadata, this.selectedPlotType);
  }

  onGoBack(id) {
    this.plotService.resetValues();
    this.router.navigate([`search/result/${id}`]);
  }

}
