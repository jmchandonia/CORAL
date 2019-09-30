import { Component, OnInit, Input, EventEmitter, Output } from '@angular/core';
import { DimensionRef } from 'src/app/shared/models/plot-builder';

@Component({
  selector: 'app-axis-labeler',
  templateUrl: './axis-labeler.component.html',
  styleUrls: ['./axis-labeler.component.css']
})
export class AxisLabelerComponent implements OnInit {

  @Input() label: string;
  @Output() labelChanged: EventEmitter<string> = new EventEmitter();

  @Input() set values(v: DimensionRef) {
    this.valueLabels = [];
    this.format = '';
    this._values = v;
    if (this.values.dimVars.length === 1) {
      this.valueLabels.push('');
      this.format = '#V1';
    } else {
      const dv = this.values.dimVars;
      dv.forEach((label, idx) => {
        this.format += `${label.value}=#V${idx + 1}`;
        if (idx !== dv.length - 1) {
          this.format += ', ';
        }
      });
      this.valueLabels = this.format.split(',').map(item => {
        return item.replace(/#V[0-9]/gi, '');
      });
    }
    this.labelChanged.emit(this.format);
  }

  get values() {
    return this._values;
  }

  displayOptions = false;
  format = '';
  invalid = false;
  valueLabels = [];
  _values: DimensionRef;

  constructor() { }

  ngOnInit() { }

  toggleDisplayOptions() {
    this.displayOptions = !this.displayOptions;
  }

  onSave() {
    this.toggleDisplayOptions();
    if (!this.displayOptions && this.format && this.format.match(/#V[0-9]/gi)) {
      this.updateFormat();
    } else {
      // if format doesn't have #V(N),  reset value labels to original state
      this.format = '';
      this.valueLabels.forEach((value, idx) => {
        this.format += `${value}#V${idx + 1},`;
      });
    }
  }

  updateFormat() {
    // get value labels to display in UI
    this.valueLabels = this.format.split(',').map(item => {
      return item.replace(/#V[0-9]/gi, '');
    });
    this.labelChanged.emit(this.format);
  }

}
