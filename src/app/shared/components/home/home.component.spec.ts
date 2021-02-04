import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { Spectator, createComponentFactory, mockProvider } from '@ngneat/spectator';
import { HomeComponent } from './home.component';
import { NgxSpinnerModule } from 'ngx-spinner';
import { HttpClientModule } from '@angular/common/http';
import { RouterModule } from '@angular/router';
import { HomeService } from 'src/app/shared/services/home.service';
import { of } from 'rxjs';
import { QueryMatch, QueryParam, QueryBuilder } from 'src/app/shared/models/QueryBuilder';
import { Router } from '@angular/router';
import { QueryBuilderService } from 'src/app/shared/services/query-builder.service';

const MockQueryBuilder = {
  getCurrentObject() { return new QueryBuilder(); }
};

const MockHomeService = {
  getProvenanceGraphData: () => {},
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
    expect(spectator.component.query.processesUp).toHaveLength(1);
    expect(spectator.component.checkBoxArray).toHaveLength(1);
    expect(spectator.component.query.processesUp[0].attribute).toBe('test attribute');

    spectator.click('input[id="0_0"]');
    expect(spectator.component.query.processesUp).toHaveLength(0);
    expect(spectator.component.checkBoxArray).toHaveLength(0);
  });

  it('should submit filters to homeService on update filter click', () => {
    const homeService = spectator.get(HomeService);
    spyOn(spectator.component, 'getUpdatedValues').and.callThrough();
    spyOn(homeService, 'getProvenanceGraphData');
    spectator.click('button#get-updated-values');
    expect(spectator.component.getUpdatedValues).toHaveBeenCalled();
    expect(homeService.getProvenanceGraphData)
      .toHaveBeenCalledWith(spectator.component.query.processesUp);
  });
});
