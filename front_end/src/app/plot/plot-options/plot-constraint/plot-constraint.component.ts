import { Component, OnInit, Input, OnChanges } from '@angular/core';
import { Constraint, ConstraintType, ConstraintVariable, UniqueValue } from 'src/app/shared/models/plotly-builder';
import { DimensionContext } from 'src/app/shared/models/object-metadata';
import { PlotService } from 'src/app/shared/services/plot.service';
import { Response } from 'src/app/shared/models/response';

@Component({
  selector: 'app-plot-constraint',
  templateUrl: './plot-constraint.component.html',
  styleUrls: ['./plot-constraint.component.css']
})
export class PlotConstraintComponent implements OnInit, OnChanges {

  @Input() constraint: Constraint;
  @Input() invalid = false;
  @Input() disabled = false;
  @Input() objectId: string;
  @Input() hideSeries = false;

  constraintTypes: string[];

  constructor(private plotService: PlotService) { }

  ngOnInit(): void {
  }

  ngOnChanges(changes) {
    if (changes['hideSeries']) {
      this.constraintTypes = Object.values(ConstraintType).filter(c => !this.hideSeries || c !== 'series');
    }
  }

  setSeriesLabel(event: 'flatten' | 'series' | 'mean', dimVar: ConstraintVariable) {
    if (event === 'series') {
      if (this.constraint.concat_variables) {
        dimVar.series_label_pattern = dimVar.value.value_with_units
          .split(',')
          .map((value, index) => value + '=#VAR' + (index + 1))
          .join(', ')
      } else {
        dimVar.series_label_pattern = dimVar.value.value_with_units + '=#VAR'
      }
    } else {
      delete dimVar.series_label_pattern;
    }
  }

  validateFormat(dimVar: ConstraintVariable) {
    if (!/\#VAR/.test(dimVar.series_label_pattern)) {
      dimVar.invalid_label_pattern = true;
    } else {
      dimVar.invalid_label_pattern = false;
    }
  }

  setSelectedValue(event: UniqueValue, dimVar: ConstraintVariable) {
    dimVar.selected_value = event?.index;
  }

  clearSelectedValue(dimVar: ConstraintVariable) {
    delete dimVar.selected_value;
  }

  handleSearch(event: any, variable: ConstraintVariable) {
    if (!this.constraint.dimension.truncate_variable_length || !event.term.length) return;
    this.plotService.getBrickDimVarValues(this.objectId, this.constraint.dim_idx, variable.dim_var_idx, event.term)
      .subscribe((res: Response<UniqueValue>) => {
        if (res.results.length < 100) {
          variable.unique_values = [...res.results];
        }
      });
  }

}
