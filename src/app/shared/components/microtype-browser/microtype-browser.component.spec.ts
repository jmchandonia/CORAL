import { async, ComponentFixture, TestBed, flushMicrotasks, fakeAsync, tick } from '@angular/core/testing';
import { NgxSpinnerModule } from 'ngx-spinner';
import { Spectator, createComponentFactory } from '@ngneat/spectator';
import { MicrotypeBrowserComponent } from './microtype-browser.component';
import { HttpClientModule } from '@angular/common/http';
// TODO: give permanent URL for mock_microtypes, this link is not in repository
const mock_microtypes = require('src/app/shared/test/mock_microtypes_3.json');
import { MicrotypeTreeService } from 'src/app/shared/services/microtype-tree.service';
import { RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { TreeModule } from 'angular-tree-component';
import { MicrotypeTreeFactoryService as MicrotypeTreeFactory } from 'src/app/shared/services/microtype-tree-factory.service';


describe('MicrotypeBrowserComponent', () => {
  let spectator: Spectator<MicrotypeBrowserComponent>;
  const createComponent = createComponentFactory({
    component: MicrotypeBrowserComponent,
    imports: [
      NgxSpinnerModule,
      HttpClientModule,
      FormsModule,
      TreeModule.forRoot(),
      RouterModule.forRoot([])
    ],
    providers: [
      {
        provide: MicrotypeTreeService,
        useValue: {
          getMicrotypes: () => Promise.resolve(MicrotypeTreeFactory.createMicrotypeTree(mock_microtypes.results))
        }
      }]
  });

  beforeEach(() => spectator = createComponent());

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
  });

  it('should have proper tree structure', async(async () => {
    const treeService = spectator.get(MicrotypeTreeService);
    spyOn(treeService, 'getMicrotypes').and.callThrough();
    await spectator.fixture.whenStable();
    spectator.component.ngOnInit();
    expect(treeService.getMicrotypes).toHaveBeenCalled();
  }));
  
  it('should have tree-root element rendered', async(() => {
    spectator.fixture.whenRenderingDone().then(
      () => {
        expect(spectator.component.tree).toBeTruthy();
        expect(spectator.query('tree-root')).not.toBeNull();
      }
    );
  }));

  it('should filter based on checkboxes', async () => {
    spyOn(spectator.component, 'setCategoryFilter').and.callThrough();
    await spectator.fixture.whenRenderingDone();
    spectator.click('input#mt_data_var');
    spectator.detectChanges();

    expect(spectator.component.filters.mt_data_var).toBeFalsy();
    expect(spectator.component.setCategoryFilter).toHaveBeenCalled();
  });

  it('should filter based on text input', async () => {
    await spectator.fixture.whenRenderingDone();
    spyOn(spectator.component, 'setKeywordSearchFilter').and.callThrough();
    spyOn(spectator.component.textInputChanged, 'next').and.callThrough();
    spectator.triggerEventHandler('input#keyword-filter', 'keyup', {target: {value: 'assembly id'}});
    spectator.detectChanges();
    expect(spectator.component.setKeywordSearchFilter).toHaveBeenCalled();
    expect(spectator.component.textInputChanged.next).toHaveBeenCalled();
    expect(spectator.query('tree-root').children).toHaveLength(1);
  });


});
