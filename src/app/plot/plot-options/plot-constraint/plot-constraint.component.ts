import { Component, OnInit, Input } from '@angular/core';
import { Constraint, ConstraintType } from 'src/app/shared/models/plotly-builder';
import { DimensionContext } from 'src/app/shared/models/object-metadata';

@Component({
  selector: 'app-plot-constraint',
  templateUrl: './plot-constraint.component.html',
  styleUrls: ['./plot-constraint.component.css']
})
export class PlotConstraintComponent implements OnInit {

  @Input() constraint: Constraint;

  constraintTypes: string[] = Object.values(ConstraintType);

  constructor() { }

  ngOnInit(): void {
  }

}
