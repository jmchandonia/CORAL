import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { BrickDimension, DimensionVariable } from 'src/app/shared/models/brick';

@Component({
  selector: 'app-dimension-variable-form',
  templateUrl: './dimension-variable-form.component.html',
  styleUrls: ['./dimension-variable-form.component.css']
})
export class DimensionVariableFormComponent implements OnInit {

  @Input() dimVar: DimensionVariable;
  @Output() deleted: EventEmitter<DimensionVariable> = new EventEmitter();
  constructor() { }

  ngOnInit() {
  }

}
