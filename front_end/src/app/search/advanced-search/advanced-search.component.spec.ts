import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { MockComponent } from 'ng-mocks';
import { AdvancedSearchComponent } from './advanced-search.component';
import { createComponentFactory, Spectator, mockProvider } from '@ngneat/spectator';
import { QueryBuilderComponent } from './query-builder/query-builder.component';
import { QueryBuilderService } from 'src/app/shared/services/query-builder.service';
import { QueryBuilder } from 'src/app/shared/models/QueryBuilder';
import { PropertyParamsComponent } from './query-builder/property-params/property-params.component';
import { HttpClientModule } from '@angular/common/http';
import { RouterModule } from '@angular/router';
import { isEqual } from 'lodash';

describe('AdvancedSearchComponent', () => {

  let spectator: Spectator<AdvancedSearchComponent>;

  const MockQueryBuilderService = {
    getCurrentObject: () => new QueryBuilder(),
    setQueryBuilderCache: () => null
  };

  const createComponent = createComponentFactory({
    component: AdvancedSearchComponent,
    declarations: [
      MockComponent(QueryBuilderComponent),
      MockComponent(PropertyParamsComponent)
    ],
    imports: [
      HttpClientModule,
      RouterModule.forRoot([])
    ],
    providers: [
      mockProvider(QueryBuilderService, MockQueryBuilderService)
    ]
  });

  beforeEach(() => spectator = createComponent());

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
  });

  it('should have access to empty query instance', () => {
    expect(spectator.component.queryBuilderObject).toEqual(new QueryBuilder());
  });

  it('should toggle advanced filters', () => {
    const [_,  parents, children] = spectator.queryAll('app-query-builder');
    expect(parents).toBeHidden();
    expect(children).toBeHidden();

    spectator.click('.data-information-header');
    expect(parents).not.toBeHidden();
    expect(children).not.toBeHidden();
  });

});
