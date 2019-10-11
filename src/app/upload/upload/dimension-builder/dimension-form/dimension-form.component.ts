import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { BrickDimension, DimensionVariable } from 'src/app/shared/models/brick';

@Component({
  selector: 'app-dimension-form',
  templateUrl: './dimension-form.component.html',
  styleUrls: ['./dimension-form.component.css']
})
export class DimensionFormComponent implements OnInit {

  select2Options: Select2Options = {
    width: '100%',
    containerCssClass: 'select2-custom-container'
  }
  @Input() dimension: BrickDimension;
  @Output() deleted = new EventEmitter();
  constructor() { }

  ngOnInit() {
  }

  addDimensionVariable() {
    this.dimension.variables.push(
      new DimensionVariable(this.dimension, this.dimension.variables.length)
      );
  }

  removeDimensionVariable(dimVar) {
    this.dimension.variables = this.dimension.variables.filter(item => item !== dimVar);
    this.dimension.resetDimVarIndices();
  }

  delete() {
    this.deleted.emit(this.dimension);
  }

}
