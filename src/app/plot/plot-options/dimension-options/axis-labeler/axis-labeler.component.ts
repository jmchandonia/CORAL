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
  private displayOptions = false;
  private format = '';
  private invalid = false;
  private valueLabels = [];
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

    if (!this.displayOptions && this.format) {
      this.updateFormat();
    }
  }

  updateFormat() {
    const newFormat = this.format.split(',');
    if (newFormat.length === this.valueLabels.length) {
      this.invalid = false;
      this.valueLabels = [...newFormat.map(item => item.replace(/#V[0-9]/gi, ''))];
      this.labelsChanged.emit(this.valueLabels);
    } else {
      this.invalid = true;
    }
  }

}
