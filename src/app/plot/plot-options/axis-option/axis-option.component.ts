import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { Axis, AxisOption } from 'src/app/shared/models/plotly-builder';
import { AxisData } from 'src/app/shared/models/plotly-config';

@Component({
  selector: 'app-axis-option',
  templateUrl: './axis-option.component.html',
  styleUrls: ['./axis-option.component.css']
})

export class AxisOptionComponent implements OnInit {

  @Input() axis: Axis; // TODO: Figure out a way to combine these 2?
  @Input() axisValidation: AxisData;
  
  public validOptions: AxisOption[];
  private _options: AxisOption[];
  @Input() set options(_options: AxisOption[]) {
    this._options = _options;
    // TODO: checking this.axisValidation in another input setter is risky
    this.validOptions = this.axisValidation.numeric_only
      ? this.options.filter(option => {
        return option.scalarType === 'float' ||
        option.scalarType === 'int' ||
        option.scalarType === 'date';
      })
      : this.options;
  }
  get options() { return this._options }

  @Input() coreType = false;
  @Input() label: string;

  @Output() selected: EventEmitter<null> = new EventEmitter();

  constructor() { }

  ngOnInit(): void {
    if (this.validOptions.length === 1) {
      this.axis.data = this.validOptions[0];
      if (this.axis.data.dimension !== undefined) {
        this.axis.dimIdx = this.axis.data.dimension;
        // this.selected.emit(this.axis.data.dimension);
        this.selected.emit();
      }
    }
  }

  setAxis(event: AxisOption) {
    this.axis.title = event.displayName;
    if (event.dimension !== undefined) {
      this.axis.dimIdx = event.dimension;
      // this.selected.emit(event.dimension);
    }
    this.selected.emit();
  }

}
