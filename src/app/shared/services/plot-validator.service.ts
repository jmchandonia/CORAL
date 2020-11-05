import { Injectable } from '@angular/core';
import { PlotlyBuilder, Constraint, ConstraintVariable } from 'src/app/shared/models/plotly-builder';

@Injectable({
  providedIn: 'root'
})
export class PlotValidatorService {

  constructor() { }

  public static validPlot(plot: PlotlyBuilder): boolean {
    if (!plot.plotType) return false;

    for(const [_, val] of Object.entries(plot.axes)) {
      if (!val.data) return false;
    }

    for (const constraint of plot.constraints) {
      if (!this.validConstraint(constraint)) return false;
    }

    return true;
  }

  static validConstraint(constraint: Constraint): boolean {
    if (constraint.constrainByMean) return true;
    for (const variable of constraint.variables) {
      if (!this.validConstraintVariable(variable)) return false;
    }
    return true;
  }

  static validConstraintVariable(variable: ConstraintVariable) : boolean {
    if (!variable.type) return false;
    if (variable.type === 'flatten' && variable.flattenValue === undefined) return false;
    return true;
  }

}