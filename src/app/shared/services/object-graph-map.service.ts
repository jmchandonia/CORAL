import { Injectable } from '@angular/core';
import { NetworkService } from './network.service';
import { ObjectMetadata, ObjectDataInfo, Dimension } from '../models/object-metadata';
import { DataQuery } from '../models/data-query';
import { FormGroup, FormArray } from '@angular/forms';

@Injectable({
  providedIn: 'root'
})
export class ObjectGraphMapService {

objectdata1 = new ObjectDataInfo({
    type: 'Microbial Growth',
    units: '',
    scalar_type: 'Number'
});

dimension1 = new Dimension({
    type: 'conditions',
    dim_vars: ['media addition', 'concentration of metal mix', 'temperature']
});

dimension2 = new Dimension({
    type: 'time since inoculation',
    dim_vars: ['hours']
});

selectedObject = new ObjectMetadata({
    id: 'brick000000123',
    type: 'brick',
    shape: [1, 2],
    name: 'microbial growth',
    data: this.objectdata1,
    dimensions: [this.dimension2, this.dimension1]
});


  // private selectedObject: ObjectMetadata = new ObjectMetadata(object1);

  private graphOptions2d = [
    'scatter',
    'bar'
  ];

  private graphOptions3d = [
    'heatmap'
  ];

  private dataQuery = new DataQuery();

  constructor(
    private network: NetworkService,
    // private dataQuery: DataQuery
    ) { }

  // get selected object

  getSelectedObject() {
    return this.selectedObject;
  }

  // set selected object

  listPlotTypes() {
    if (this.selectedObject.shape.length > 2) {
      return null;
    } else {
      return this.selectedObject.shape.length === 1 ?
        this.graphOptions2d : this.graphOptions3d;
    }
  }

  setDimension(axis, dimension) {
    this.dataQuery[axis] = parseInt(dimension, 10);
  }

  submitNewPlot(plot: FormGroup) {
    const dims = plot.get('dimensions') as FormArray;
    const obj = this.selectedObject;
    const body: any = {
      id: this.selectedObject.id,
      x_dimension: {
        dimension: obj.dimensions.indexOf(dims[0].get('fromDimension')),
        dim_vars: this.selectedObject.dimensions.filter(d => dims[0].get('displayValuesFrom'))
      }
    };
    if (dims[2]) {
      body.z_direction = this.selectedObject.dimensions.indexOf(dims[2]);
    }
  }

}
