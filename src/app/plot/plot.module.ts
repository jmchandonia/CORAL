import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { PlotComponent } from './plot.component';
import { PlotRoutingModule } from './plot-routing.module';
import { PlotOptionsComponent } from './plot-options/plot-options.component';
import { Select2Module } from 'ng2-select2';
import { DimensionOptionsComponent } from './plot-options/dimension-options/dimension-options.component';
import { ReactiveFormsModule } from '@angular/forms';
@NgModule({
  declarations: [PlotComponent, PlotOptionsComponent, DimensionOptionsComponent],
  imports: [
    CommonModule,
    PlotRoutingModule,
    Select2Module,
    ReactiveFormsModule
  ]
})
export class PlotModule { }
