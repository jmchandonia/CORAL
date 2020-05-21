import { Component, OnInit, Input, ChangeDetectorRef } from '@angular/core';
import { Dimension } from '../../../shared/models/plot-builder';
import { Select2OptionData } from 'ng2-select2';
import { PlotService } from '../../../shared/services/plot.service';
import { DimensionContext, ArrayContext, TypedValue } from 'src/app/shared/models/object-metadata';
// tslint:disable:variable-name
@Component({
  selector: 'app-dimension-options',
  templateUrl: './dimension-options.component.html',
  styleUrls: [
    '../plot-options.component.css',
    './dimension-options.component.css'
  ]
})
export class DimensionOptionsComponent implements OnInit {

  @Input() set  dimension(dim: Dimension) {
    this._dimension = dim;
    dim.dimensionMetadata.forEach((dimContext: DimensionContext, index: number) => {
      const { oterm_name, oterm_ref } = dimContext.data_type;
      this.dropdownValues.push({id: index.toString(), text: oterm_name}); // context will go here.text
    });
    const dataVar = dim.dataValueMetadata[0];
    this.dropdownValues.push({id: 'D', text: dataVar.value_type.oterm_name});
  }

  get dimension() { return this._dimension; }
  @Input() dimensionLabel: string; // label for form UI e.g. 'X axis'

  dropdownValues: Array<Select2OptionData> = [{id: '', text: ''}];
  _dimension: Dimension;
  showDisplayValues = false;

  select2Options: Select2Options = {
    width: '100%',
    containerCssClass: 'select2-custom-container',
    placeholder: 'Select Dimension'
  };

  @Input() set index(i: number) {
    // map index order to key value pairs for server
    const xyz = ['x', 'y', 'z'];
    this.axis = xyz[i];
  }

  axis: string; // reference to plotly data axis in plotbuilder
  selectedDropdownValue: string;
  dimVars: TypedValue[];

  constructor(private plotService: PlotService, public chRef: ChangeDetectorRef) { }

  ngOnInit() {
    this.selectedDropdownValue = this.plotService.getDimDropdownValue(this.axis);
  }

  setSelectedDimension(event) {
    const idx = parseInt(event.value, 10);
    this.plotService.setPlotlyDataAxis(this.axis, event.value);

    if (event.value === 'D') { // event value is a data var
      this.dimension.dimVars = this.dimension.dataValueMetadata;
    } else {
      this.dimension.dimVars = this.dimension.dimensionMetadata[idx].typed_values;
    }
    this.dimension.dimVars.forEach(dimVar => dimVar.selected = true);
    this.showDisplayValues = this.dimension.dimVars.length > 1;
    this.setLabelPattern();

  }

  setLabelPattern() {
    this.dimension.label_pattern = ''; // reset value
    if (this.dimension.dimVars.length === 1) {
      this.dimension.label_pattern = '#V1';
    } else {
      this.dimension.dimVars.forEach((dimVar: TypedValue, idx: number) => {
        this.dimension.label_pattern += `${dimVar.value_no_units}=#V${idx + 1}`;
        if (idx < this.dimension.dimVars.length - 1) {
          this.dimension.label_pattern += ', ';
        }
      });
    }
    this.chRef.detectChanges();
  }

}
