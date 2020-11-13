import { Component, OnInit, Input } from '@angular/core';
import { Constraint, ConstraintType, ConstraintVariable } from 'src/app/shared/models/plotly-builder';
import { DimensionContext } from 'src/app/shared/models/object-metadata';

@Component({
  selector: 'app-plot-constraint',
  templateUrl: './plot-constraint.component.html',
  styleUrls: ['./plot-constraint.component.css']
})
export class PlotConstraintComponent implements OnInit {

  @Input() constraint: Constraint;
  @Input() invalid = false;

  constraintTypes: string[] = Object.values(ConstraintType);

  constructor() { }

  ngOnInit(): void {
  }

  setSelectedValue(event, dimVar: ConstraintVariable) {
    dimVar.selected_value = dimVar.unique_values.indexOf(event as never); // TODO: get rid of type never
  }

}
