import { Component, OnInit, Input } from '@angular/core';
import { MapBuilder } from 'src/app/shared/models/map-builder';
import { CoreTypeAxis } from 'src/app/shared/models/core-type-plot-builder';

@Component({
  selector: 'app-map-options',
  templateUrl: './map-options.component.html',
  styleUrls: ['./map-options.component.css']
})
export class MapOptionsComponent implements OnInit {

  @Input() mapBuilder: MapBuilder;
  // @Input() colorOptions: CoreTypeAxis[];
  // @Input() labelOptions: CoreTypeAxis[];
  @Input() set options(_options: CoreTypeAxis[]) {
    this.labelOptions = _options;
    this.colorOptions = [..._options.filter(option => option.scalar_type === 'float' || option.scalar_type === 'int')]
  }

  public labelOptions: CoreTypeAxis[];
  public colorOptions: CoreTypeAxis[];

  constructor() { }

  ngOnInit(): void {
  }
}
