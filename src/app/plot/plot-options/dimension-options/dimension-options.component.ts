import { Component, OnInit, Input, EventEmitter } from '@angular/core';
import { Dimension } from '../../../shared/models/object-metadata';
import { Select2OptionData } from 'ng2-select2';
import { ObjectGraphMapService } from '../../../shared/services/object-graph-map.service';

@Component({
  selector: 'app-dimension-options',
  templateUrl: './dimension-options.component.html',
  styleUrls: [
    '../plot-options.component.css',
    './dimension-options.component.css'
  ]
})
export class DimensionOptionsComponent implements OnInit {

  @Input() set dimensions(d: Dimension[]) {
    this.allDimensions = d;
    d.forEach((val, idx) => {
      this.fromDimensionDropdown.push({id: idx.toString(), text: val.type});
    });
  }
  @Input() dimensionLabel = '';
  selectedValue: Dimension;
  allDimensions: Dimension[];
  fromDimensionDropdown: Array<Select2OptionData> = [{id: '', text: ''}];

  constructor(
    private objectGraphMap: ObjectGraphMapService
  ) { }

  ngOnInit() {
  }

  setSelectedDimension(event) {
    this.selectedValue = this.allDimensions[event.value];
    this.objectGraphMap.setDimension(this.dimensionLabel, event.value);
  }

}
