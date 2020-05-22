import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { Spectator, createComponentFactory, mockProvider } from '@ngneat/spectator';
import { HomeComponent } from './home.component';
import { NgxSpinnerModule } from 'ngx-spinner';
import { HttpClientModule } from '@angular/common/http';
import { RouterModule } from '@angular/router';
import { HomeService } from 'src/app/shared/services/home.service';
import { of } from 'rxjs';
import { QueryMatch, QueryParam } from 'src/app/shared/models/QueryBuilder';
import { Router } from '@angular/router';
import { QueryBuilderService } from 'src/app/shared/services/query-builder.service';

const MockQueryBuilder = {
  submitSearchResultsFromHome: (queryMatch: QueryMatch) => {}
};

const MockHomeService = {
  getUpdatedValues: () => of({
    results: {
      core_types: {
        items: [
          {count: 300, name: 'test core type 1', queryMatch: new QueryMatch()},
          {count: 275, name: 'test core type 2', queryMatch: new QueryMatch()}
        ]
      },
      dynamic_types: {
        items: [
          {count: 3, name: 'test dynamic type 1', queryMatch: new QueryMatch()}
        ]
      }
    },
    status: 'OK'
  }),
  getFilterValues: () => of({
    results: [
      {
        categoryName: 'ENIGMA Campaigns',
        items: [
          {
            name: 'test campaign 1',
            queryParam: new QueryParam(
              'test attribute',
              'test match',
              'test keyword',
              'test scalar'
            )
          },
          {
            name: 'test campaign 2',
            queryParam: new QueryParam()
          }
        ]
      },
      {
        categoryName: 'ENIGMA Personnel',
        items: [
          {
            name: 'test personnel 1',
            queryParam: new QueryParam()
          },
          {
            name: 'test personnel 1',
            queryParam: new QueryParam()
          },
        ]
      }
    ]
  })
};

describe('HomeComponent', () => {
  let spectator: Spectator<HomeComponent>;
  const createComponent = createComponentFactory({
    component: HomeComponent,
    imports: [
      NgxSpinnerModule,
      HttpClientModule,
      RouterModule.forRoot([])
    ],
    providers: [
      mockProvider(HomeService, MockHomeService),
      mockProvider(QueryBuilderService, MockQueryBuilder),
      {
        provide: Router,
        useValue: {navigate: () => {}}
      }
    ]
  });

  beforeEach(() => spectator = createComponent());

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
  });

  it('should render filters', () => {
    const spy = spyOn(MockHomeService, 'getFilterValues').and.callThrough();

    expect(spectator.queryAll('.filter-box > ul > li')).toHaveLength(2);
    expect(spectator.queryAll('.checkbox-container > input')).toHaveLength(4);
    expect(spectator.query('.filter-box > ul > li > span')).toHaveText('ENIGMA Campaigns');
    expect(spectator.query('.checkbox-container > label')).toHaveText('test campaign 1');
    expect(spectator.query('.checkbox-container > input')).toHaveId('0_0');
  });

  it('should add value on value checked', () => {
    spyOn(MockHomeService, 'getFilterValues').and.callThrough();

    spectator.click('input[id="0_0"]');
    expect(spectator.component.filterQueryBuilder).toHaveLength(1);
    expect(spectator.component.checkBoxArray).toHaveLength(1);
    expect(spectator.component.filterQueryBuilder[0].attribute).toBe('test attribute');

    spectator.click('input[id="0_0"]');
    expect(spectator.component.filterQueryBuilder).toHaveLength(0);
    expect(spectator.component.checkBoxArray).toHaveLength(0);
  });

  it('should render core objects and dynamic type list', () => {
    spyOn(MockHomeService, 'getUpdatedValues').and.callThrough();
    expect(spectator.queryAll('.core-objects-container > ul > li')).toHaveLength(2);
    expect(spectator.queryAll('.data-sets-container > ul > li')).toHaveLength(1);
    expect(spectator.query('.core-objects-container > ul > li > span')).toHaveText('test core type 1');
    expect(spectator.query('.core-objects-container > ul > li > span:nth-child(2)')).toHaveText('300');
  });
});
