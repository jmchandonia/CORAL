import { Injectable } from '@angular/core';
import { NetworkService } from './network.service';
import { PlotBuilder, Dimension, Config } from '../models/plot-builder';
import { DataQuery } from '../models/data-query';
import { FormGroup, FormArray } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { Subject } from 'rxjs';
import { DimensionRef } from 'src/app/shared/models/plot-builder';

@Injectable({
  providedIn: 'root'
})
export class PlotService {

  public plotBuilder: PlotBuilder = new PlotBuilder();
  public plotType: string;
  public axisLabelBuilders: any = {};
  private axisLabelSub = new Subject();

  constructor(private http: HttpClient) { }

  getPlotBuilder() {
    return this.plotBuilder;
  }

  getPlotType() {
    return this.plotType;
  }

  setPlotType(value) {
    this.plotType = value;
  }

  getConfiguredDimensions() {
    const keys = Object.keys(this.plotBuilder.config);
    // return all refenences to dimensions without adding config.title
    return keys.map(v => this.plotBuilder.config[v]).filter(t => typeof t !== 'string');
  }

  getDimDropdownValue(axis) {
    return this.plotBuilder.data[axis];
  }

  setConfig(
    title: string,
    length: number,
    callback: (dims: Dimension[]) => void
    ) {
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
  }

  /// axis label methods ///

  setLabelBuilder(labelBuilder: DimensionRef, axis: string) {
    this.axisLabelBuilders[axis] = labelBuilder;
    this.axisLabelSub.next({axis, labelBuilder: this.axisLabelBuilders[axis]});
  }

  getLabelBuilder(axis) {
    return this.axisLabelBuilders[axis];
  }

  getUpdatedLabelBuilder() {
    return this.axisLabelSub.asObservable();
  }

  updateFormatString(format: string, axis: string) {
    this.plotBuilder.config[axis].label_pattern = format;
  }

  clearPlotBuilder() {
    delete this.plotType;
    this.axisLabelBuilders = {};
    this.plotBuilder = new PlotBuilder();
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
