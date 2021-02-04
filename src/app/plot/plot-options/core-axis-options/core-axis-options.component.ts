import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { CoreTypeAxis } from 'src/app/shared/models/core-type-plot-builder';

@Component({
  selector: 'app-core-axis-options',
  templateUrl: './core-axis-options.component.html',
  styleUrls: ['./core-axis-options.component.css']
})
export class CoreAxisOptionsComponent implements OnInit {

  @Input() public showTitle = true;
  @Input() public axisOptions: CoreTypeAxis[];
  axis: string;
  title: string;
  @Input() set index(i: number) {
    const axes = ['x', 'y', 'z'];
    this.axis = axes[i];
  }

  @Output() onAxisSelection: EventEmitter<any> = new EventEmitter();
  @Output() onAxisTitleSelection: EventEmitter<any> = new EventEmitter();
  @Output() onShowTitleChange: EventEmitter<any> = new EventEmitter();

  constructor() { }

  ngOnInit(): void {
  }

  setAxis(event) {
    this.onAxisSelection.emit({axis: this.axis, value: event});
    this.onAxisTitleSelection.emit({axis: this.axis, value: event.name + (event.units ? ` (${event.units})` : '')});
    this.title = event.name + (event.units ? ` (${event.units})` : '');
  }

  setTitle(event) {
    this.onAxisTitleSelection.emit({axis: this.axis, value: event.target.value});
    this.title = event.target.value;
  }

  setShowTitle() {
    this.onShowTitleChange.next({axis: this.axis, value: this.showTitle});
  }

}
