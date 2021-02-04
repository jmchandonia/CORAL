import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { PlotComponent } from './plot.component';
import { PlotOptionsComponent } from './plot-options/plot-options.component';
import { PlotResultComponent } from './plot-result/plot-result.component';
import { AuthGuardService as AuthGuard } from '../shared/services/auth-guard.service';
import { MapResultComponent } from './map-result/map-result.component';

const routes: Routes = [
  {
    path: 'plot', component: PlotComponent, canActivate: [AuthGuard], children: [
      { path: '', redirectTo: 'options/:id', pathMatch: 'full' },
      { path: 'options', component: PlotOptionsComponent },
      { path: 'options/:id', component: PlotOptionsComponent },
      { path: 'result', component: PlotResultComponent },
      { path: 'result/:id', component: PlotResultComponent },
      { path: 'map/result', component: MapResultComponent }
    ]
  }
];

@NgModule({
  declarations: [],
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class PlotRoutingModule { }