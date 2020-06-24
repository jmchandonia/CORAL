import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { Spectator, createComponentFactory, mockProvider } from '@ngneat/spectator';
import { SearchResultComponent } from './search-result.component';
import { RouterModule } from '@angular/router';
import { NgxSpinnerModule } from 'ngx-spinner';
import { HttpClientModule } from '@angular/common/http';
import { QueryBuilderService } from 'src/app/shared/services/query-builder.service';
import { Subject } from 'rxjs';
import { QueryBuilder, QueryParam } from 'src/app/shared/models/QueryBuilder'; 

describe('SearchResultComponent', () => {

  const mockResultsSub = new Subject();
  const mockQueryBuilder = new QueryBuilder();
  mockQueryBuilder.processesUp.push(new QueryParam());

  const MockQueryBuilder = {
    getSearchResults: () => mockResultsSub.asObservable(),
    getCurrentObject: () => mockQueryBuilder
  };

  let spectator: Spectator<SearchResultComponent>
  const createComponent = createComponentFactory({
    component: SearchResultComponent,
    imports: [
      RouterModule.forRoot([]),
      NgxSpinnerModule,
      HttpClientModule
    ],
    providers: [
      mockProvider(QueryBuilderService, MockQueryBuilder)
    ]
  });

  beforeEach(() => spectator = createComponent());

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
  });

  it('should render results table dynamically', () => {
    const spy = spyOn(MockQueryBuilder, 'getSearchResults').and.callThrough();
    mockResultsSub.next({
        data: [
          {value1: '1', value2: '2', value3: '3'},
          {value1: '4', value2: '5', value3: '6'}
        ],
        schema: {
          fields:  ['value1', 'value2', 'value3']
        }
      });
    spectator.detectChanges();
    expect(spectator.query('table')).not.toBeNull();
    expect(spectator.queryAll('table > thead > tr > th').length).toBe(4);
    expect(spectator.queryAll('table > tbody > tr').length).toBe(2);
  });

  it('should have access to query builder object', () => {
    spyOn(MockQueryBuilder, 'getCurrentObject').and.callThrough();
    expect(spectator.component.searchQuery).toBeTruthy();
    expect(spectator.component.searchQuery.processesUp.length).toBe(1);
  });

  it('should render search query JSON in pre tag', () => {
    expect(spectator.query('.query-container')).toBeNull();
    // expect(spectator.query('.menu-option col-2')).toHaveText('Show Query');

    spectator.click('.menu-option.col-2');
    expect(spectator.query('.query-container')).not.toBeNull();
    // expect(spectator.query('.menu-option col-2')).toHaveText('Hide Query');
  });
});
