import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { Spectator, createComponentFactory } from '@ngneat/spectator';
import { SearchResultItemComponent } from './search-result-item.component';
import { ProcessDataComponent } from '../process-data/process-data.component';
import { MockComponent } from 'ng-mocks';
import { HttpClientModule } from '@angular/common/http';
import { RouterModule } from '@angular/router';
import { BsModalService, BsModalRef } from 'ngx-bootstrap';
import { ModalModule } from 'ngx-bootstrap/modal';

describe('SearchResultItemComponent', () => {
  // let component: SearchResultItemComponent;
  // let fixture: ComponentFixture<SearchResultItemComponent>;

  // beforeEach(async(() => {
  //   TestBed.configureTestingModule({
  //     declarations: [ SearchResultItemComponent ]
  //   })
  //   .compileComponents();
  // }));

  // beforeEach(() => {
  //   fixture = TestBed.createComponent(SearchResultItemComponent);
  //   component = fixture.componentInstance;
  //   fixture.detectChanges();
  // });
  let spectator: Spectator<SearchResultItemComponent>;
  const createComponent = createComponentFactory({
    component: SearchResultItemComponent,
    entryComponents: [
      MockComponent(ProcessDataComponent)
    ],
    imports: [
      HttpClientModule,
      RouterModule.forRoot([]),
      ModalModule.forRoot()
    ],
    providers: [
      BsModalService
    ]
  });

  beforeEach(() => spectator = createComponent());

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
  });
});
