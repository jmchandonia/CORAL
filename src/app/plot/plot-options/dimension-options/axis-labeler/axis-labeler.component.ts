import { Component, OnInit, Input, EventEmitter, Output } from '@angular/core';

@Component({
  selector: 'app-axis-labeler',
  templateUrl: './axis-labeler.component.html',
  styleUrls: ['./axis-labeler.component.css']
})
export class AxisLabelerComponent implements OnInit {

  @Input() set values(v) {
    this.valueLabels = v;
    this.valueLabels.forEach((value, idx)  => {
      this.format += `${value}=#V${idx},`;
      value += '=';
    });
  }
  displayOptions = false;
  format = '';
  invalid = false;
  valueLabels = [];
  @Output() labelsChanged: EventEmitter<any> = new EventEmitter();

  constructor() { }

  ngOnInit() { }

  toggleDisplayOptions() {
    this.displayOptions = !this.displayOptions;
    if (this.displayOptions && !this.format) {
      this.valueLabels.forEach((v, i) => {
        this.format += `${v}#V${i + 1}, `;
      });
    }
  }

  onSave() {
    this.toggleDisplayOptions();
    if (!this.displayOptions && this.format) {
      this.updateFormat();
    }
  }

  updateFormat() {

    // get key value format to send to server, eg {0: 'value=#V1'}
    const newFormat = this.format.split(',').map(item => {
      const index = parseInt(item.replace(/^\D+/g, ''), 10) - 1;
      return { [index]: item };
    });
    if (NaN in newFormat[newFormat.length - 1]) {
      newFormat.pop();
    }
    // get value labels to display in UI
    const newValueLabels = this.format.split(',').map(item => {
      return item.replace(/#V[0-9]/gi, '');
    });

    if (!newValueLabels[newValueLabels.length - 1].match(/#V[0-9]/gi)) {
      newValueLabels.pop();
    }
    this.valueLabels = newValueLabels;
    this.labelsChanged.emit(this.format);
  }

}
