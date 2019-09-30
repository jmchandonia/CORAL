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
          [...dim.typed_values.map(t => ({ value: t.value_type.oterm_name, selected: true }))]
        )
      );
    });
    // add measurement value
    const measurementVal = data.data_type.oterm_name;
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
  }

  plotlyDataRef: string; // reference to plotly data axis in plotbuilder
  dimensionData: DimensionRef[] = []; // used to display dimension variable value and title
  selectedDimension: DimensionRef;

  constructor(private plotService: PlotService, private chRef: ChangeDetectorRef) { }

  ngOnInit() {
  }

  setSelectedDimension(event) {
    const idx = parseInt(event.value, 10);
    if (idx === this.dimensionData.length - 1) {
      // measurement option is seleceted, set value in service to 'D'
      this.plotService.setPlotlyDataAxis(this.plotlyDataRef, 'D');
    } else {
      // otherwise set plotly ref as index value
      this.plotService.setPlotlyDataAxis(this.plotlyDataRef, event.value);
    }
    this.selectedDimension = this.dimensionData[idx];
    this.dimension.title = this.selectedDimension.type;
    this.chRef.detectChanges();
  }

  updateLabelPattern(value) {
    // updated label pattern from axis labeler component
    this.dimension.label_pattern = value;
  }

}
