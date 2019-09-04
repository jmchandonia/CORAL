import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { PlotComponent } from './plot.component';
import { PlotRoutingModule } from './plot-routing.module';
import { PlotOptionsComponent } from './plot-options/plot-options.component';

@NgModule({
  declarations: [PlotComponent, PlotOptionsComponent],
  imports: [
    CommonModule,
    PlotRoutingModule
  ]
})
export class PlotModule { }
