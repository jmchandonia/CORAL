import { Component, OnInit, Input, EventEmitter } from '@angular/core';
import { Dimension, DimensionRef } from '../../../shared/models/plot-builder';
import { Select2OptionData } from 'ng2-select2';
import { PlotService } from '../../../shared/services/plot.service';
// import { FormGroup, FormControl, FormArray } from '@angular/forms';

@Component({
  selector: 'app-dimension-options',
  templateUrl: './dimension-options.component.html',
  styleUrls: [
    '../plot-options.component.css',
    './dimension-options.component.css'
  ]
})
export class DimensionOptionsComponent implements OnInit {


  @Input() dimension: Dimension; // reference to dimension in plot service
  @Input() dimensionLabel: string; // label for form UI e.g. 'X axis'
  @Input() dropdownValues: Array<Select2OptionData> = [{id: '', text: ''}];
  @Input() set metadata(data: any) {
    data.dim_context.forEach(dim => {
      // add dimension labels and variables
      this.dimensionData.push(
        new DimensionRef(
          dim.data_type.oterm_name,
          [...dim.typed_values.map(type => ({ value: type.oterm_name, selected: true }))]
        )
      );
    });
    // add measurement value
    const measurementVal = data.typed_values[0].value_type.oterm_name;
    this.dimensionData.push(
      new DimensionRef(
        measurementVal, [{value: measurementVal, selected: true}]
      )
    );
  }

  @Input() set index(i: number) {
    // map index order to key value pairs for server
    const xyz = ['x', 'y', 'z'];
    this.plotlyDataRef = xyz[i];
    console.log('PLOTLY DATA REF', this.plotlyDataRef);
  }

  plotlyDataRef: string; // reference to plotly data axis in plotbuilder
  dimensionData: DimensionRef[] = []; // used to display dimension variable value and title
  selectedDimension: DimensionRef;

  constructor(private plotService: PlotService) { }

  ngOnInit() {
    console.log('DIMENSION', this.dimension);
    console.log('DIMENSION LABEL', this.dimensionLabel);
  }

  setSelectedDimension(event) {
    // IMPORTANT -> check if server will accept index submissions as strings
    const idx = parseInt(event.value, 10);
    if (idx === this.dimensionData.length - 1) {
      // measurement option is seleceted, set value in service to 'D'
      this.plotService.setPlotlyDataAxis(this.plotlyDataRef, 'D');
    } else {
      // otherwise set plotly ref as index value
      this.plotService.setPlotlyDataAxis(this.plotlyDataRef, event.value);
    }
    this.selectedDimension = this.dimensionData[idx];
  }

  updateLabelPattern(value) {
    this.dimension.label_pattern = value;
  }

  // @Input() set dropdownValues(d: any[]) {
  //   this.fromDimensionDropdown = [{id: '', text: ''}, ...d];
  // }

  // get dimensions() {
  //   return this._dimensions;
  // }

  // @Input() index: number;
  // @Input() dimensionLabel = '';
  // @Input() metadata: any;
  // selectedValue: any;
  // _dimensions: Dimension[];
  // fromDimensionDropdown: Array<Select2OptionData> = [{id: '', text: ''}];
  // fromDimensionDropdownId: string;
  // // displayValuesFrom: FormArray;
  // // displayAxisLabelsAs: FormArray;
  // labelsChecked = [];
  // axisTitle: string;

  // constructor(
  //   private plotService: PlotService
  // ) { }

  // ngOnInit() {
  //   console.log('METADATA', this.metadata);
  //   // this.displayAxisLabelsAs = this.form.get('displayAxisValuesAs') as FormArray;
  //   // if (this.plotService.plotForm) {
  //   //   const f = this.plotService.plotForm.value.dimensions[this.index];
  //   //   this.fromDimensionDropdownId = this.fromDimensionDropdown.find(item => item.text === f.fromDimension).id;
  //   //   this.selectedValue = this.dimensions[this.fromDimensionDropdownId];
  //   //   if (parseInt(this.fromDimensionDropdownId, 10) === this.fromDimensionDropdown.length - 2) {
  //   //     this.axisTitle = this.metadata.typed_values[0].value_type.oterm_name;
  //   //     if (this.metadata.typed_values[0].value_units) {
  //   //       this.axisTitle += `(${this.metadata.typed_values[0].value_units.oterm_name})`;
  //   //     }
  //   //   } else {
  //   //     const idx = parseInt(this.fromDimensionDropdownId, 10);
  //   //     this.axisTitle = this.metadata.dim_context[idx].data_type.oterm_name;
  //   //   }
  //   //   this.addDimensionVariables(f.fromDimension);
  //   // }

  //   console.log('DIMENSION', this.dimension);

  //  }

  // setSelectedDimension(event) {
  //   const idx = parseInt(event.value, 10);
  //   this.dimension.fromDimension = event.data[0].text;
  //   // if selected value is data measurements (at the end of the dropdown)
  //   if (idx === this.fromDimensionDropdown.length - 2) {
  //     this.selectedValue = this.metadata.typed_values[0];
  //     console.log('SELECTED VALUE yes', this.selectedValue);
  //     this.selectedValue.dim_vars = [];
  //     this.axisTitle = `${this.metadata.typed_values[0].value_type.oterm_name}`;

  //     // add units if there are any
  //     if (this.metadata.typed_values[0].value_units) {
  //       this.axisTitle += ` (${this.metadata.typed_values[0].value_units.oterm_name})`;
  //     }
  //   } else {
  //     console.log('SELECTED VALUE NO', this.selectedValue);
  //     // if selected value is from a dimension in the brick
  //     this.selectedValue = this.metadata.dim_context[idx];
  //     const dim = this.metadata.dim_context[idx];
  //     // this.selectedValue = {
  //     //   type: dim.data_type.oterm_name,
  //     //   dim_vars: [...dim.typed_values.map(x => x.value_type.oterm_name)]
  //     // };
  //     this.axisTitle = `${this.metadata.dim_context[idx].data_type.oterm_name}`;
  //   }
  //   this.addDimensionVariables(event.data[0].text);
  // }

  // addDimensionVariables(label)  {
  //   // this.displayValuesFrom = this.form.get('displayValuesFrom') as FormArray;
  //   // this.displayAxisLabelsAs = this.form.get('displayAxisLabelsAs') as FormArray;

  //   // clear form value on select
  //   // while (this.displayValuesFrom.length) {
  //   //   this.displayValuesFrom.removeAt(0);
  //   // }

  //   // add new values from selected dimension

  //   const { dim_vars } = this.selectedValue;

  //   if (this.selectedValue.dim_vars.length > 1) {
  //     dim_vars.forEach((dim, idx) => {
  //       const stringPattern = `${dim}=#V${idx + 1}, `;
  //       this.dimension.labelPattern += stringPattern;
  //       this.labelsChecked.push(stringPattern);
  //     });
  //   } else {
  //     // prepopulate axis labeler if there's only one dimension variable
  //     this.dimension.labelPattern = '#V1';
  //     this.labelsChecked = [`#V1`];
  //     // this.setNewLabels(`#V1`);
  //   }
  // }

  // isChecked(index) {
  //   return this.displayValuesFrom.at(index).value;
  // }

  // editAxisLabels(index) {
  //   this.resetAxisLabels();
  //   const newVar = this.selectedValue.dim_vars[index] + '=';
  //   if (this.isChecked(index)) {
  //     this.labelsChecked.push(newVar);
  //     this.displayAxisLabelsAs.push(new FormControl(newVar));
  //   } else {
  //     this.labelsChecked = this.labelsChecked.filter(item => {
  //       return item !== newVar;
  //     });
  //     this.labelsChecked.forEach(label => this.displayAxisLabelsAs.push(new FormControl(label)));
  //   }
  // }

  // findVariableNumber(value) {
  //   return this.labelsChecked.indexOf(value + '=') + 1;
  // }

  // resetAxisLabels() {
  //   while (this.displayAxisLabelsAs.length) {
  //     this.displayAxisLabelsAs.removeAt(0);
  //   }
  // }

  // get displayValues() {
  //   return this.displayValuesFrom;
  // }

  // get isDisplayAxisChecked() {
  //   return this.form.get('displayAxisLabels').value;
  // }

  // get isDisplayHoverChecked() {
  //   return this.form.get('displayHoverLabels').value;
  // }

  // setNewLabels(labels) {
  //   console.log('WHEN IS THIS HAPPENING');
  // }

  // d() {
  //   console.log(this.selectedValue);
  // }

}
