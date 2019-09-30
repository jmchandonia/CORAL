import { Injectable } from '@angular/core';
import { NetworkService } from './network.service';
import { PlotBuilder, Dimension, Config } from '../models/plot-builder';
import { DataQuery } from '../models/data-query';
import { FormGroup, FormArray } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { Subject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class PlotService {

  public plotBuilder: PlotBuilder = new PlotBuilder();

  constructor(private http: HttpClient) { }

  getPlotBuilder() {
    return this.plotBuilder;
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

  clearPlotBuilder() {
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
