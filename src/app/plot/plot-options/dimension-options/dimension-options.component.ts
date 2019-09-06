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
    this.allDimensions = d;
    d.forEach((val, idx) => {
      this.fromDimensionDropdown.push({id: idx.toString(), text: val.type});
    });
  }
  @Input() index: number;
  @Input() set form(f: FormGroup) {
    // tslint:disable-next-line:no-string-literal
    this.dimensionForm = f.controls.dimensions['controls'][this.index];
  }
  @Input() dimensionLabel = '';
  selectedValue: Dimension;
  allDimensions: Dimension[];
  fromDimensionDropdown: Array<Select2OptionData> = [{id: '', text: ''}];
  dimensionForm: FormGroup;
  displayValuesFrom: FormArray;

  constructor(
    private objectGraphMap: ObjectGraphMapService
  ) { }

  ngOnInit() { }

  setSelectedDimension(event) {
    this.selectedValue = this.allDimensions[event.value];
    this.dimensionForm.controls.fromDimension.setValue(event.data[0].text);
    this.addDimensionVariables();
  }

  addDimensionVariables()  {
    this.displayValuesFrom = this.dimensionForm.get('displayValuesFrom') as FormArray;

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
      this.displayValuesFrom.push(new FormControl(true));
    }
  }

  get displayValues() {
    return this.displayValuesFrom;
  }

  get isDisplayAxisChecked() {
    return this.dimensionForm.get('displayAxisLabels').value;
  }

  get isDisplayHoverChecked() {
    return this.dimensionForm.get('displayHoverLabels').value;
  }

  updateDimensionVariable(event) {
  }

}
