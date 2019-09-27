import { Injectable } from '@angular/core';
import { NetworkService } from './network.service';
// import { ObjectMetadata, ObjectDataInfo } from '../models/object-metadata';
import { PlotBuilder, Dimension, Config } from '../models/plot-builder';
import { DataQuery } from '../models/data-query';
import { FormGroup, FormArray } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { Subject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class PlotService {

  // dataQuery = new DataQuery();
  // plotData: any[];
  // plotDataSub = new Subject();
  // plotRequestBody: any;
  // public plotType: any;
  // public plotForm: FormGroup;
  // public plotFormDimensions: FormArray;

  // public plotBuilder: PlotBuilder = new PlotBuilder();

  // constructor(
  //   private network: NetworkService,
  //   private http: HttpClient
  //   ) { }

  // setDimension(axis, dimension) {
  //   this.dataQuery[axis] = parseInt(dimension, 10);
  // }

  // getPlotData() {
  //   return this.plotData;
  // }

  // getPlotDataSub() {
  //   return this.plotDataSub.asObservable();
  // }

  // resetValues() {
  //   this.plotForm = undefined;
  //   this.plotType = undefined;
  // }

  // submitNewPlot(formGroup: FormGroup, metadata: any, plotTypeData: any) {
  //   const form = formGroup.value;
  //   const xyzLabels = ['x', 'y', 'z'];

  //   const body = {
  //     objectId: metadata.id,
  //     data: {},
  //     config: {
  //       title: form.graphTitle,
  //     },
  //     plotly_trace: plotTypeData.plotly_trace,
  //     plotly_layout: plotTypeData.plotly_layout,
  //   };

  //   form.dimensions.forEach((dim, idx) => {
  //     const xyz = xyzLabels[idx];
  //     if (dim.fromDimension === metadata.typed_values[0].value_type.oterm_name) {
  //       body.data[xyz] = 'D';
  //     } else {
  //       const matchDim = metadata.dim_context.find(item => item.data_type.oterm_name === dim.fromDimension);
  //       const dimIdx = metadata.dim_context.indexOf(matchDim);
  //       body.data[xyz] = dimIdx;
  //       body.config[xyz] = {
  //         title: dim.axisTitle,
  //         label_pattern: dim.displayAxisLabelsAs[0],
  //         show_title: dim.displayAxisLabels,
  //         show_labels: dim.displayHoverLabels
  //       };
  //     }
  //   });

  //   this.plotRequestBody = body;
  //   this.plotForm = formGroup;
  //   this.plotFormDimensions = formGroup.controls.dimensions as FormArray;
  //   this.plotType = plotTypeData;
  // }

  // getPlotType() {
  //   return this.plotForm;
  // }

  // getPlotlyData() {
  //   return this.http.post<any>('https://psnov1.lbl.gov:8082/generix/plotly_data', this.plotRequestBody);
  // }


  public plotBuilder: PlotBuilder = new PlotBuilder();

  constructor(private http: HttpClient) { }

  getPlotBuilder() {
    return this.plotBuilder;
  }

  plotBuilderTest() { console.log(this.plotBuilder); }

  setConfig(title: string, length: number, callback: (dims: Dimension[]) => void) {
    const { config } = this.plotBuilder;
    config.title = title;
    config.x = new Dimension();
    config.y = new Dimension();
    if (length > 1) {
      config.z = new Dimension();
      this.plotBuilder.data.z = '';
      callback([config.x, config.y, config.z]); // add 3 dimensions to form
    } else {
      callback([config.x, config.y]); // add 2 dimensions to form
    }
    console.log('PLOT BUILDER', this.plotBuilder);
  }

  setPlotlyDataAxis(key: string, value: string) {
    this.plotBuilder.data[key] = value;
  }

  getPlotlyData() {
    return this.http.post<any>('https://psnov1.lbl.gov:8082/generix/plotly_data', this.plotBuilder);
  }

  getPlotTypes() {
    return this.http.get('https://psnov1.lbl.gov:8082/generix/plot_types');
  }




}
