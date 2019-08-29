import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { PlotComponent } from './plot.component';
import { SimpleSearchComponent } from './simple-search/simple-search.component';
import { AdvancedSearchComponent } from './advanced-search/advanced-search.component';

const routes: Routes = [
  { 
    path: 'plot', component: PlotComponent, children: [
      {path: '', redirectTo: 'search', pathMatch: 'full'},
      {path: 'search', component: SimpleSearchComponent},
      {path: 'search/advanced', component: AdvancedSearchComponent}
    ]
 }
];

@NgModule({
  declarations: [],
  imports: [
    RouterModule.forChild(routes)
  ],
  exports: [RouterModule]
})
export class PlotRoutingModule { }
