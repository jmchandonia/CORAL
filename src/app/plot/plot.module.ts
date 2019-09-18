import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { PlotComponent } from './plot.component';
import { PlotRoutingModule } from './plot-routing.module';
import { PlotOptionsComponent } from './plot-options/plot-options.component';
import { Select2Module } from 'ng2-select2';
import { DimensionOptionsComponent } from './plot-options/dimension-options/dimension-options.component';
import { ReactiveFormsModule, FormsModule } from '@angular/forms';
import { AxisLabelerComponent } from './plot-options/dimension-options/axis-labeler/axis-labeler.component';
import { PlotResultComponent } from './plot-result/plot-result.component';
import { PlotlyModule } from 'angular-plotly.js';
import * as PlotlyJS from 'plotly.js/dist/plotly.js';

import { ObjectGraphMapService } from '../shared/services/object-graph-map.service';

PlotlyModule.plotlyjs = PlotlyJS;
@NgModule({
  declarations: [PlotComponent, PlotOptionsComponent, DimensionOptionsComponent, AxisLabelerComponent, PlotResultComponent],
  imports: [
    CommonModule,
    PlotRoutingModule,
    Select2Module,
    ReactiveFormsModule,
    FormsModule,
    PlotlyModule
  ],
  providers: [ObjectGraphMapService]
})
export class PlotModule { }
