import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { BrickDimension, DimensionVariable } from 'src/app/shared/models/brick';

@Component({
  selector: 'app-dimension-form',
  templateUrl: './dimension-form.component.html',
  styleUrls: ['./dimension-form.component.css']
})
export class DimensionFormComponent implements OnInit {

  @Input() dimension: BrickDimension;
  @Output() deleted = new EventEmitter();
  constructor() { }

  ngOnInit() {
  }

  delete() {
    this.deleted.emit(this.dimension);
  }

}
