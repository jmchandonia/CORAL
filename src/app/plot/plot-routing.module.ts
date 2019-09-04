import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { PlotComponent } from './plot.component';
import { PlotOptionsComponent } from './plot-options/plot-options.component';

const routes: Routes = [
  {
    path: 'plot', component: PlotComponent, children: [
      { path: '', redirectTo: 'options/:id', pathMatch: 'full' },
      { path: 'options/:id', component: PlotOptionsComponent }
    ] 
  }
]

@NgModule({
  declarations: [],
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class PlotRoutingModule { }