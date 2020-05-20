import { Component, OnInit, Input, OnChanges, SimpleChanges } from '@angular/core';
import { Dimension } from 'src/app/shared/models/plot-builder';
import { TypedValue } from 'src/app/shared/models/object-metadata';

@Component({
  selector: 'app-axis-labeler',
  templateUrl: './axis-labeler.component.html',
  styleUrls: ['./axis-labeler.component.css'],
})
export class AxisLabelerComponent implements OnInit, OnChanges {


  @Input() dimVars: TypedValue[];
  @Input() dimension: Dimension;
  @Input() labelPattern: string;
  plotlyFormatString: string;
  displayOptions = false;

  constructor() { }

  ngOnInit() {
    this.dimension.dimVars.forEach((dimVar) => {
      // set selected value for checkbox
      if (dimVar.selected === undefined) {
        dimVar.selected = true;
      }
    });
    this.plotlyFormatString = this.dimension.label_pattern;
  }

  ngOnChanges(changes: SimpleChanges) {
    if (changes.labelPattern) {
      this.plotlyFormatString = changes.labelPattern.currentValue;
    }
  }

  setLabels() {
    this.dimension.label_pattern = this.plotlyFormatString;
  }

  updateSelectedLabels(index: number) {
    const strIdx = (index + 1).toString();
    if (this.dimension.label_pattern.includes(strIdx)) {
      // filter out variables
      this.dimension.label_pattern = this.dimension.label_pattern
        .split(',')
        .filter(label => !label.includes(strIdx))
        .join();
    } else {
      // add new variable to label pattern
      const dimVar = this.dimension.dimVars[index];
      this.dimension.label_pattern += `, ${dimVar.value_no_units}=#V${strIdx}`;
    }
    this.plotlyFormatString = this.dimension.label_pattern;
  }

  get labelDisplay(): string[] {
    return this.dimension.label_pattern.split(',')
      .map((label) => {
        const idx = label.indexOf('#V') + 2;
        const varIdx = label[idx];
        const htmlString = `<span>${label}</span>`
          .replace(/#V[0-9]/gi, `<span class="badge badge-pill badge-primary">V${varIdx}</span>`);
        return htmlString;
      });
  }

  toggleDisplayOptions() {
    this.displayOptions = !this.displayOptions;
  }

}
