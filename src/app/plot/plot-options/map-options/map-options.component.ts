import { Component, OnInit, Input } from '@angular/core';
import { MapBuilder } from 'src/app/shared/models/map-builder';
import { CoreTypeAxis } from 'src/app/shared/models/core-type-plot-builder';
import { AxisOption } from 'src/app/shared/models/plotly-builder';

@Component({
  selector: 'app-map-options',
  templateUrl: './map-options.component.html',
  styleUrls: ['./map-options.component.css']
})
export class MapOptionsComponent implements OnInit {

  @Input() mapBuilder: MapBuilder;
  @Input() options: AxisOption[];

  constructor() { }

  ngOnInit(): void {
  }
}
