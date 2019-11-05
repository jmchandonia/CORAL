import { Component, OnInit, Input, ChangeDetectorRef } from '@angular/core';
import { Dimension, DimensionRef } from '../../../shared/models/plot-builder';
import { Select2OptionData } from 'ng2-select2';
import { PlotService } from '../../../shared/services/plot.service';

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
          [...dim.typed_values.map(t => ({ value: t.value_type.oterm_name, selected: true, context: t.value_context }))]
        )
      );
    });
    // add measurement value, for now we are only working with one data value
    const measurementVal = data.typed_values[0];
    this.dimensionData.push(
      new DimensionRef(
        measurementVal, [{value: measurementVal.value_type.oterm_name, selected: true, context: measurementVal.value_context }]
      )
    );
  }

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
  dimensionData: DimensionRef[] = []; // used to display dimension variable value and title
  selectedDimension: DimensionRef;
  selectedDropdownValue: string;

  constructor(private plotService: PlotService, public chRef: ChangeDetectorRef) { }

  ngOnInit() {
    this.selectedDropdownValue = this.plotService.getDimDropdownValue(this.axis);
    this.selectedDimension = this.plotService.getLabelBuilder(this.axis);
  }

  setSelectedDimension(event) {
    const idx = parseInt(event.value, 10);
    this.plotService.setPlotlyDataAxis(this.axis, event.value);
    if (event.value === 'D') {
      this.selectedDimension = this.dimensionData[this.dimensionData.length - 1];
    } else {
      this.selectedDimension = this.dimensionData[idx];
    }
    this.plotService.setLabelBuilder(this.selectedDimension, this.axis);
    // this.dimension.title = this.selectedDimension.type;

    if (this.selectedDimension.dimVars.length > 1) {
      this.dimension.title = this.selectedDimension.type;
    } else {
      const { dimVars } = this.selectedDimension;
      this.dimension.title = dimVars[0].value;
      dimVars[0].context.forEach(ctx => {
        this.dimension.title += `, ${ctx.value_type.oterm_name}=${ctx.value.value}`;
        if (ctx.units) {
          this.dimension.title += `(${ctx.units.oterm_name})`;
        }
      });
    }

    // hide dimension variable options if theres only one variable;
    this.showDisplayValues = this.selectedDimension.dimVars.length > 1;
    this.chRef.detectChanges();
  }

  updateLabelPattern(value) {
    // updated label pattern from axis labeler component
    this.dimension.label_pattern = value;
  }

}
