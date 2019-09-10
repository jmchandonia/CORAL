import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { PlotComponent } from './plot.component';
import { PlotOptionsComponent } from './plot-options/plot-options.component';
import { PlotResultComponent } from './plot-result/plot-result.component';

const routes: Routes = [
  {
    path: 'plot', component: PlotComponent, children: [
      { path: '', redirectTo: 'options/:id', pathMatch: 'full' },
      { path: 'options/:id', component: PlotOptionsComponent },
      { path: 'result', component: PlotResultComponent },
    ]
  }
];

@NgModule({
  declarations: [],
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class PlotRoutingModule { }