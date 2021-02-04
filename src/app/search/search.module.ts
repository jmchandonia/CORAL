import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { SearchRoutingModule } from './search-routing.module';
import { SearchComponent } from './search.component';
import { SimpleSearchComponent } from './simple-search/simple-search.component';
import { AdvancedSearchComponent } from './advanced-search/advanced-search.component';
import { QueryBuilderComponent } from './advanced-search/query-builder/query-builder.component';
import { PropertyParamsComponent } from './advanced-search/query-builder/property-params/property-params.component';
import { FormsModule } from '@angular/forms';
import { SearchResultComponent } from './search-result/search-result.component';
import { HttpClientModule } from '@angular/common/http';
import { SearchResultItemComponent } from './search-result/search-result-item/search-result-item.component';
import { QueryBuilderService } from '../shared/services/query-builder.service';
import { SearchResultCoreItemComponent } from './search-result/search-result-core-item/search-result-core-item.component';
import { ProcessDataComponent } from './search-result/process-data/process-data.component';
import { NgxSpinnerModule } from 'ngx-spinner';
import { DimensionVariablePreviewComponent } from './search-result/dimension-variable-preview/dimension-variable-preview.component';
import { NgSelectModule } from '@ng-select/ng-select';
import { ProcessFilterComponent } from './advanced-search/process-filter/process-filter.component';
import { BsDatepickerModule } from 'ngx-bootstrap/datepicker';
import { NgxDatatableModule } from '@swimlane/ngx-datatable';
import { ModalModule } from 'ngx-bootstrap/modal';
import { ImageDisplayComponent } from './search-result/image-display/image-display.component';

@NgModule({
  declarations: [
    SearchComponent,
    SimpleSearchComponent,
    AdvancedSearchComponent,
    QueryBuilderComponent,
    PropertyParamsComponent,
    SearchResultComponent,
    SearchResultItemComponent,
    SearchResultCoreItemComponent,
    ProcessDataComponent,
    DimensionVariablePreviewComponent,
    ProcessFilterComponent,
    ImageDisplayComponent
  ],
  imports: [
    CommonModule,
    SearchRoutingModule,
    FormsModule,
    HttpClientModule,
    NgxSpinnerModule,
    NgSelectModule,
    BsDatepickerModule.forRoot(),
    NgxDatatableModule,
    ModalModule.forRoot()
  ],
  providers: [QueryBuilderService],
  bootstrap: [DimensionVariablePreviewComponent]
})
export class SearchModule { }
