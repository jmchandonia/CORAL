import { Component, OnInit, Input, EventEmitter } from '@angular/core';

@Component({
  selector: 'app-dimension-options',
  templateUrl: './dimension-options.component.html',
  styleUrls: [
    '../plot-options.component.css',
    './dimension-options.component.css'
  ]
})
export class DimensionOptionsComponent implements OnInit {

  @Input() dimension = '';
  dimensionVariables = [
    'Media Addition', 
    'Concentration of Nitrate',
    'Carbon Source',
    'Presence of Metal Mix'
  ];

  constructor() { }

  ngOnInit() {
  }

}
