import { async, fakeAsync, ComponentFixture, TestBed, tick } from '@angular/core/testing';
import { RouterModule } from '@angular/router';
import { HttpClientModule } from '@angular/common/http';
import { ProcessFilterComponent } from './process-filter.component';
import { Spectator, createComponentFactory, mockProvider } from '@ngneat/spectator';
import { of } from 'rxjs'; 
import { QueryBuilderService } from 'src/app/shared/services/query-builder.service';
import { QueryParam } from 'src/app/shared/models/QueryBuilder';

describe('ProcessFilterComponent', () => {

  let spectator: Spectator<ProcessFilterComponent>;

  const mockQueryBuilder = {
    getProcessOterms() {
      return of({
        // results: ['process 1', 'process 2', 'process 3']
        retults: [
          {id: 'process1', text: 'process 1'}
        ]
      });
    },
    getCampaignOterms() {
      return of({
        results: ['campaign 1', 'campaign 2', 'campaign 3']
      });
    },
    getPersonnelOterms() {
      return of({
        results: ['person 1', 'person 2', 'person 3']
      });
    },
  };

  let mockQueryParams: QueryParam[] = [];

  const createComponent = createComponentFactory({
    component: ProcessFilterComponent,
    imports: [
      HttpClientModule,
      RouterModule.forRoot([])
    ],
    providers: [
      {
        provide: QueryBuilderService,
        useValue: mockQueryBuilder
      }
    ]
  });

  beforeEach(() => spectator = createComponent({
    props: {
      queryParams: mockQueryParams
    }
  }));

  it('should create and call oterm getter methods', () => {

    const queryBuilder = spectator.get(QueryBuilderService);
    const getProcessSpy = spyOn(queryBuilder, 'getProcessOterms').and.callThrough();
    const getCampaignSpy = spyOn(queryBuilder, 'getCampaignOterms').and.callThrough();
    const getPersonnelSpy = spyOn(queryBuilder, 'getPersonnelOterms').and.callThrough();
    spectator.detectChanges();

    expect(spectator.component).toBeTruthy();
    expect(getProcessSpy);
    expect(getCampaignSpy);
    expect(getPersonnelSpy);
  });

  it('should add new query params', () => {
    spyOn(spectator.component, 'addFilter').and.callThrough();
    spectator.triggerEventHandler('ng-select#processes', 'change', {id: 'x', text: 'x'});
    spectator.triggerEventHandler('ng-select#campaigns', 'change', {id: 'y', text: 'y'});
    spectator.triggerEventHandler('ng-select#personnel', 'change', {id: 'z', text: 'z'});

    expect(spectator.component.addFilter).toHaveBeenCalledTimes(3);
    expect(spectator.component.queryParams).toHaveLength(3);
    expect(spectator.component.queryParams[2]).toEqual(new QueryParam('person', '=', 'z', 'string'));
  });

  it('should remove query params', () => {
    spyOn(spectator.component, 'addFilter').and.callThrough();
    spectator.triggerEventHandler('ng-select#campaigns', 'change', null);

    expect(spectator.component.addFilter).toHaveBeenCalled();
    expect(spectator.component.queryParams).toHaveLength(2);
    expect(spectator.component.queryParams[1]).toEqual(new QueryParam('person', '=', 'z', 'string'));

    spectator.component.queryParams = [];
    spectator.component.queryParams.length = 0;
    mockQueryParams = [
      new QueryParam('date_start', '=', '2020-03-15', 'string'),
      new QueryParam('date_end', '=', '2020-06-24', 'string')
    ]
  });

  it('should persist data', () => {
    expect(spectator.component.date_start.keyword).toBe('2020-03-15');
    expect(spectator.component.date_end.keyword).toBe('2020-06-24');
  });

});
