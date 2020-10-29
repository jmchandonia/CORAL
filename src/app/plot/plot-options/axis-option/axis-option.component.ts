import { Component, OnInit, Input } from '@angular/core';
import { Axis, AxisOption } from 'src/app/shared/models/plotly-builder';

@Component({
  selector: 'app-axis-option',
  templateUrl: './axis-option.component.html',
  styleUrls: ['./axis-option.component.css']
})
export class AxisOptionComponent implements OnInit {

  @Input() axis: Axis;
  @Input() options: AxisOption[];
  @Input() coreType = false;
  @Input() label: string;

  constructor() { }

  ngOnInit(): void {
  }

  setAxis(event: AxisOption) {
    this.axis.title = event.displayName;
  }

}
