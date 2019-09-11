import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { SearchComponent } from './search.component';
import { SimpleSearchComponent } from './simple-search/simple-search.component';
import { AdvancedSearchComponent } from './advanced-search/advanced-search.component';
import { SearchResultComponent } from './search-result/search-result.component';
import { SearchResultItemComponent } from './search-result/search-result-item/search-result-item.component';

const routes: Routes = [
  {
    path: 'search', component: SearchComponent, children: [
      {path: '', redirectTo: 'simple', pathMatch: 'full'},
      {path: 'simple', component: SimpleSearchComponent},
      {path: 'advanced', component: AdvancedSearchComponent},
      {path: 'result', component: SearchResultComponent},
      {path: 'result/:id', component: SearchResultItemComponent}
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
export class SearchRoutingModule { }
