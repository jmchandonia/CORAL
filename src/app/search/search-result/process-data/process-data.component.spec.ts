import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { Spectator, createComponentFactory, mockProvider } from '@ngneat/spectator';
import { ProcessDataComponent } from './process-data.component';
import { RouterModule } from '@angular/router';
import { HttpClientModule } from '@angular/common/http';
import { of } from 'rxjs';
import { QueryBuilderService } from 'src/app/shared/services/query-builder.service';
import { ActivatedRoute } from '@angular/router';

describe('ProcessDataComponent', () => {

  const setNumberOfDocs = (n: number) => Array(n).fill({
    category: 'category',
    description: 'description',
    id: 'process00000',
    type: 'type'
  });

  let numberOfDocs = 1;

  const MockQueryBuilder = {
    getProcessesUp: () => of({
      results: [
        {
        docs: setNumberOfDocs(numberOfDocs),
        process: {
          campaign: 'campaign',
          date_start: '01/01/1970',
          date_end: '01/09/2038',
          id: 'ProcessXXXXXXX',
          person: 'Person Lab',
          process: 'XXXXX Sequencing'
        }
      }
    ]
    }),
    getProcessesDown: () => of({
      results: [
        {
          docs: [{
            category: 'category',
            derscription: 'description',
            id: 'process0000',
            type: 'type'
        }],
        process: {
          campaign: 'campaign',
          date_start: '01/01/1970',
          date_end: '01/09/2038',
          id: 'ProcessXXXXXXX',
          person: 'Person Lab',
          process: 'XXXXX Sequencing'
        }
      },
    ]
    })
  };



  let spectator: Spectator<ProcessDataComponent>;
  const createComponent = createComponentFactory({
    component: ProcessDataComponent,
    imports: [
      RouterModule.forRoot([]),
      HttpClientModule
    ],
    providers: [
      {
        provide: ActivatedRoute,
        useValue: {
          params: of({id: 'brick0000000'})
        }
      },
      mockProvider(QueryBuilderService, MockQueryBuilder)
    ]
  });

  beforeEach(() => spectator = createComponent());

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
  });

  it('should should get processes up and down', () => {
    expect(spectator.component.processesDown).toHaveLength(1);
    expect(spectator.component.processesUp).toHaveLength(1);
  });


});
