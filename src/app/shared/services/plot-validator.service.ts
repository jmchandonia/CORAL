import { Injectable } from '@angular/core';
import { PlotlyBuilder, Constraint, ConstraintVariable } from 'src/app/shared/models/plotly-builder';

@Injectable({
  providedIn: 'root'
})
export class PlotValidatorService {

  constructor() { }

  public static validPlot(plot: PlotlyBuilder): boolean {
    if (!plot.plot_type) return false;

    for(const [_, val] of Object.entries(plot.axes)) {
      if (!val.data) return false;
    }

    for (const constraint of plot.constraints) {
      if (!this.validConstraint(constraint)) return false;
    }

    return true;
  }

  static validConstraint(constraint: Constraint): boolean {
    if (constraint.constrain_by_mean) return true;
    for (const variable of constraint.variables) {
      if (!this.validConstraintVariable(variable)) return false;
    }
    return true;
  }

  static validConstraintVariable(variable: ConstraintVariable) : boolean {
    if (!variable.type) return false;
    if (variable.type === 'flatten' && variable.flatten_value === undefined) return false;
    return true;
  }

}