import { Component, OnInit, Input, EventEmitter } from '@angular/core';
import { Dimension } from '../../../shared/models/object-metadata';
import { Select2OptionData } from 'ng2-select2';
import { ObjectGraphMapService } from '../../../shared/services/object-graph-map.service';
import { FormGroup, FormControl, FormArray } from '@angular/forms';

@Component({
  selector: 'app-dimension-options',
  templateUrl: './dimension-options.component.html',
  styleUrls: [
    '../plot-options.component.css',
    './dimension-options.component.css'
  ]
})
export class DimensionOptionsComponent implements OnInit {

  @Input() set dimensions(d: Dimension[]) {
    this._dimensions = d;
    d.forEach((val, idx) => {
      this.fromDimensionDropdown.push({id: idx.toString(), text: val.type});
    });
  }

  get dimensions() {
    return this._dimensions;
  }

  @Input() index: number;
  @Input() form: FormGroup;
  @Input() dimensionLabel = '';
  @Input() metadata: any;
  selectedValue: Dimension;
  _dimensions: Dimension[];
  fromDimensionDropdown: Array<Select2OptionData> = [{id: '', text: ''}];
  displayValuesFrom: FormArray;
  displayAxisLabelsAs: FormArray;
  isLabelChecked = [];
  axisTitle: string;

  constructor(
    objectGraphMap: ObjectGraphMapService
  ) { }

  ngOnInit() {
    this.displayAxisLabelsAs = this.form.get('displayAxisValuesAs') as FormArray;
   }

  setSelectedDimension(event) {
    this.selectedValue = this.dimensions[event.value];
    this.form.controls.fromDimension.setValue(event.data[0].text);

    // if selected value is data measurements (at the end of the dropdown)
    if (parseInt(event.value, 10) === this.fromDimensionDropdown.length - 2) {
      this.axisTitle = `${this.metadata.typed_values[0].value_type.oterm_name}`;

      // add units if there are any
      if (this.metadata.typed_values[0].value_units) {
        this.axisTitle += ` (${this.metadata.typed_values[0].value_units.oterm_name})`;
      }
    } else {
      // if selected value is from a dimension in the brick
      const idx = parseInt(event.value, 10);
      this.axisTitle = `${this.metadata.dim_context[idx].data_type.oterm_name}`;
    }
    this.addDimensionVariables(event.data[0].text);
  }

  addDimensionVariables(label)  {
    this.displayValuesFrom = this.form.get('displayValuesFrom') as FormArray;
    this.displayAxisLabelsAs = this.form.get('displayAxisLabelsAs') as FormArray;

    // clear form value on select
    while (this.displayValuesFrom.length) {
      this.displayValuesFrom.removeAt(0);
    }

    // add new values from selected dimension
    if (this.selectedValue.dim_vars.length > 1) {
      this.selectedValue.dim_vars.forEach(() => {
        this.displayValuesFrom.push(new FormControl(false));
      });
    } else {
      // prepopulate axis labeler if there's only one dimension variable
      this.displayValuesFrom.push(new FormControl({value: true, disabled: true}));
      this.setNewLabels(`${label}=#V1`);
      this.isLabelChecked = [`${label}=`];
    }
  }

  isChecked(index) {
    return this.displayValuesFrom.at(index).value;
  }

  editAxisLabels(index) {
    this.resetAxisLabels();
    const newVar = this.selectedValue.dim_vars[index] + '=';
    if (this.isChecked(index)) {
      this.isLabelChecked.push(newVar);
      this.displayAxisLabelsAs.push(new FormControl(newVar));
    } else {
      this.isLabelChecked = this.isLabelChecked.filter(item => {
        return item !== newVar;
      });
      this.isLabelChecked.forEach(label => this.displayAxisLabelsAs.push(new FormControl(label)));
    }
  }

  findVariableNumber(value) {
    return this.isLabelChecked.indexOf(value + '=') + 1;
  }

  resetAxisLabels() {
    while (this.displayAxisLabelsAs.length) {
      this.displayAxisLabelsAs.removeAt(0);
    }
  }

  get displayValues() {
    return this.displayValuesFrom;
  }

  get isDisplayAxisChecked() {
    return this.form.get('displayAxisLabels').value;
  }

  get isDisplayHoverChecked() {
    return this.form.get('displayHoverLabels').value;
  }

  setNewLabels(labels) {
    while (this.displayAxisLabelsAs.length) {
      this.displayAxisLabelsAs.removeAt(0);
    }
    this.displayAxisLabelsAs.push(new FormControl(labels));
  }

}
