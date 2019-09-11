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
import { SearchResultComponent } from './search-result/search-result.component';
import { HttpClientModule } from '@angular/common/http';


@NgModule({
  declarations: [
    SearchComponent, 
    SimpleSearchComponent, 
    AdvancedSearchComponent, 
    QueryBuilderComponent, PropertyParamsComponent, SearchResultComponent
  ],
  imports: [
    CommonModule,
    SearchRoutingModule,
    Select2Module,
    FormsModule,
    HttpClientModule
  ]
})
export class SearchModule { }
