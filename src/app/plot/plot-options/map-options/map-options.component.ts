import { Component, OnInit, Input } from '@angular/core';
import { MapBuilder } from 'src/app/shared/models/map-builder';
import { CoreTypeAxis } from 'src/app/shared/models/core-type-plot-builder';
import { AxisOption } from 'src/app/shared/models/plotly-builder';
import { DimensionContext } from 'src/app/shared/models/object-metadata';

@Component({
  selector: 'app-map-options',
  templateUrl: './map-options.component.html',
  styleUrls: ['./map-options.component.css']
})
export class MapOptionsComponent implements OnInit {

  labelOptions: AxisOption[];
  colorOptions: AxisOption[];
  public invalid = false;

  @Input() dimensions: DimensionContext[];
  @Input() mapBuilder: MapBuilder;
  @Input() set options(options: AxisOption[]) {
    this.labelOptions = options.filter(option => {
      return option.data_variable !== undefined || option.dimension === this.mapBuilder.dimWithCoords;
    });
    this.colorOptions = options.filter(option => {
      // only allow user to color pins by numeric value or by category (things like unique ids or names not allowed)
      if (option.data_variable === undefined && option.dimension !== this.mapBuilder.dimWithCoords) {
        return false;
      }
      const { scalar_type } = option;
      return scalar_type === 'float' || scalar_type === 'int' || scalar_type === 'date' || scalar_type === 'term';
    })
  }

  constructor() { }

  ngOnInit(): void {
  }

  setColorOptions(event) {
    if (!event) {
      delete this.mapBuilder.colorFieldScalarType;
    } else {
      // map will handle coloring pins differently depending on if its a nubmer or a term
      this.mapBuilder.colorFieldScalarType = event.scalar_type;
    }
    if (!this.mapBuilder.isCoreType) {
      this.mapBuilder.setConstraints(this.dimensions);
    }
  }

  setLabelOptions(event) {
    if (!this.mapBuilder.isCoreType) {
      this.mapBuilder.setConstraints(this.dimensions);
    }
  }

}
