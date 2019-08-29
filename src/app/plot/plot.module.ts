import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { PlotRoutingModule } from './plot-routing.module';
import { PlotComponent } from './plot.component';
import { SimpleSearchComponent } from './simple-search/simple-search.component';
import { AdvancedSearchComponent } from './advanced-search/advanced-search.component';
import { Select2Module } from 'ng2-select2';
import { QueryBuilderComponent } from './advanced-search/query-builder/query-builder.component';
import { PropertyParamsComponent } from './advanced-search/query-builder/property-params/property-params.component';

@NgModule({
  declarations: [
    PlotComponent, 
    SimpleSearchComponent, 
    AdvancedSearchComponent, 
    QueryBuilderComponent, PropertyParamsComponent
  ],
  imports: [
    CommonModule,
    PlotRoutingModule,
    Select2Module
  ]
})
export class PlotModule { }
