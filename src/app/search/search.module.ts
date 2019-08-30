import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { SearchRoutingModule } from './search-routing.module';
import { SearchComponent } from './search.component';
import { SimpleSearchComponent } from './simple-search/simple-search.component';
import { AdvancedSearchComponent } from './advanced-search/advanced-search.component';
import { Select2Module } from 'ng2-select2';
import { QueryBuilderComponent } from './advanced-search/query-builder/query-builder.component';
import { PropertyParamsComponent } from './advanced-search/query-builder/property-params/property-params.component';
import { FormsModule } from '@angular/forms';


@NgModule({
  declarations: [
    SearchComponent, 
    SimpleSearchComponent, 
    AdvancedSearchComponent, 
    QueryBuilderComponent, PropertyParamsComponent
  ],
  imports: [
    CommonModule,
    SearchRoutingModule,
    Select2Module,
    FormsModule
  ]
})
export class SearchModule { }
